# ─────────────────────────────────────────────────────────────────────────────
#  Shiritori — Network Edition  ✦ cosmic nebula theme
#  pip install customtkinter
#
#  pyinstaller --onefile --windowed
#    --add-data "words_dictionary.json;."
#    --add-data "C:\path\to\customtkinter;customtkinter"
#    shiritori_net.py
# ─────────────────────────────────────────────────────────────────────────────

import customtkinter as ctk
import random, json, socket, threading, sys, os

PORT = 55731

def resource_path(f):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, f)

def config_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "shiritori_cfg.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "shiritori_cfg.json")

def load_config():
    try:
        with open(config_path()) as f: return json.load(f)
    except Exception: return {}

def save_config(data):
    try:
        with open(config_path(), "w") as f: json.dump(data, f)
    except Exception: pass

def load_ip_history():  return load_config().get("ip_history", [])

def save_ip_to_history(ip):
    cfg = load_config()
    h = cfg.get("ip_history", [])
    if ip in h: h.remove(ip)
    h.insert(0, ip)
    cfg["ip_history"] = h[:10]
    save_config(cfg)

try:
    with open(resource_path("words_dictionary.json")) as f:
        dictionary = set(json.load(f).keys())
except FileNotFoundError:
    dictionary = set()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── cosmic nebula palette ─────────────────────────────────────────────────────
BG       = "#07050F"   # near-void black with violet undertone
CARD     = "#0D0818"   # dark indigo — card surface
CARD2    = "#130E24"   # slightly elevated surface
BORDER   = "#2D1B54"   # deep violet border (subtle)
BORDER_A = "#6D28D9"   # active/glowing border
ACCENT   = "#A855F7"   # neon purple — primary glow
GLOW     = "#C084FC"   # lighter lavender — highlights
RED      = "#F472B6"   # soft pink-red (not harsh, stays cosmic)
RED_B    = "#EC4899"   # brighter pink for urgent states
GREEN    = "#34D399"   # muted teal-green (success)
ORANGE   = "#FB923C"   # warm amber (warning)
DIM      = "#5B4D7A"   # muted violet-gray
TEXT     = "#EDE9FE"   # pale lavender-white

def _F(size, weight="normal"):
    return ctk.CTkFont(size=size, weight=weight)

def _card(parent, border_color=None, corner=12, **kw):
    return ctk.CTkFrame(parent, corner_radius=corner, fg_color=CARD,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _card2(parent, border_color=None, **kw):
    return ctk.CTkFrame(parent, corner_radius=10, fg_color=CARD2,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _btn(parent, text, command, color=None, size=13, **kw):
    c = color or ACCENT
    return ctk.CTkButton(
        parent, text=text, font=_F(size, "bold"), command=command,
        corner_radius=10, fg_color=CARD2,
        hover_color="#1E1035",
        border_width=1, border_color=c, text_color=c, **kw)

def _btn_solid(parent, text, command, size=13, **kw):
    return ctk.CTkButton(
        parent, text=text, font=_F(size, "bold"), command=command,
        corner_radius=10, fg_color="#4C1D95",
        hover_color="#5B21B6",
        text_color=TEXT, **kw)

def _entry(parent, placeholder="", **kw):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        font=_F(13), corner_radius=10,
        fg_color=CARD2, border_color=BORDER, border_width=1,
        text_color=TEXT, placeholder_text_color=DIM, **kw)

def _lbl(parent, text, size=13, color=None, weight="normal", **kw):
    return ctk.CTkLabel(
        parent, text=text, font=_F(size, weight),
        text_color=color or TEXT, **kw)

def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=BORDER, corner_radius=0).pack(
        fill="x", padx=14, pady=6)


# ══════════════════════════════════════════════════════════════════════════════
#  NETWORKING
# ══════════════════════════════════════════════════════════════════════════════

def send_msg(sock, obj):
    data = json.dumps(obj).encode()
    sock.sendall(len(data).to_bytes(4, "big") + data)

def recv_msg(sock):
    def recvall(n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk: return None
            buf += chunk
        return buf
    try:
        hdr = recvall(4)
        if not hdr: return None
        return json.loads(recvall(int.from_bytes(hdr, "big")))
    except Exception: return None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"


# ══════════════════════════════════════════════════════════════════════════════
#  GAME SERVER
# ══════════════════════════════════════════════════════════════════════════════

class GameServer:
    def __init__(self, num_players, on_event):
        self.num_players    = num_players
        self.on_event       = on_event
        self.clients        = {}
        self.lock           = threading.Lock()
        self.scores         = [0] * num_players
        self.active_players = list(range(1, num_players + 1))
        self.wordlist       = ["apple"]
        self.forbidden      = chr(random.randint(ord("a"), ord("z")))
        self.current_player = 1
        self.previous_word  = "apple"
        self._timer_gen     = 0

    def listen(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("", PORT)); self.srv.listen(self.num_players)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        count = 0
        while count < self.num_players:
            try: conn, _ = self.srv.accept()
            except Exception: break
            count += 1; pnum = count
            with self.lock: self.clients[pnum] = conn
            send_msg(conn, {"type":"welcome","player_num":pnum,"num_players":self.num_players})
            self.on_event({"type":"player_joined","count":count})
            threading.Thread(target=self._client_loop, args=(pnum,conn), daemon=True).start()
        self._broadcast({**self._state(),"type":"game_start"})
        self._start_timer()

    def _client_loop(self, pnum, conn):
        while True:
            msg = recv_msg(conn)
            if msg is None:
                with self.lock: self._handle_disconnect(pnum)
                break
            if msg.get("type") == "action":
                with self.lock: self._handle_action(pnum, msg["word"])

    def _handle_disconnect(self, pnum):
        if pnum not in self.active_players: return
        next_p = self._next() if self.current_player == pnum else self.current_player
        self.active_players.remove(pnum); self.clients.pop(pnum, None)
        note = f"Player {pnum} disconnected."
        if len(self.active_players) == 1:
            self._stop_timer()
            self._broadcast({**self._state(),"type":"game_end","winner":self.active_players[0],"msg":note})
        elif len(self.active_players) == 0:
            self._stop_timer()
        else:
            if self.current_player == pnum: self.current_player = next_p
            self._broadcast({**self._state(),"type":"state_update","msg":note,"color":ORANGE})
            self._start_timer()

    def _handle_action(self, pnum, word):
        if pnum != self.current_player: return
        if word == "/skip": self._do_skip(pnum)
        elif word.startswith("/donate"): self._do_donate(pnum, word)
        else: self._process_word(pnum, word)

    def _process_word(self, pnum, word):
        if word in self.wordlist:
            self._send_to(pnum,{"type":"msg","text":"Already used — pick a different word.","color":RED}); return
        if dictionary and word not in dictionary:
            self._send_to(pnum,{"type":"msg","text":f'"{word}" is not a valid English word.',"color":RED}); return
        if word[0] != self.previous_word[-1]:
            self._send_to(pnum,{"type":"msg","text":f'Word must start with "{self.previous_word[-1]}".',"color":RED}); return
        if word[-1] == self.forbidden:
            next_p = self._next(); self.active_players.remove(pnum)
            msg = f"Player {pnum} is out! Ended with forbidden letter '{self.forbidden}'."
            if len(self.active_players) == 1:
                self._stop_timer()
                self._broadcast({**self._state(),"type":"game_end","winner":self.active_players[0],"msg":msg})
            else:
                self.current_player = next_p
                self._broadcast({**self._state(),"type":"state_update","msg":msg,"color":RED_B})
                self._start_timer()
            return
        self.wordlist.append(word); self.scores[pnum-1] += len(word)
        self.previous_word = word; self.current_player = self._next()
        self._broadcast({**self._state(),"type":"state_update",
                         "msg":f"Player {pnum}: '{word}'  +{len(word)} pts","color":GREEN})
        self._start_timer()

    def _do_skip(self, pnum):
        o = random.randint(0, 2)
        if o == 0:
            self.scores[pnum-1] = max(0, self.scores[pnum-1]-10)
            msg, col = f"Player {pnum} skipped — lost 10 pts.", ORANGE
        elif o == 1:
            msg, col = f"Player {pnum} skipped safely — no penalty.", GREEN
        else:
            next_p = self._next(); self.active_players.remove(pnum)
            msg = f"Player {pnum} skipped and got eliminated!"
            if len(self.active_players) == 1:
                self._stop_timer()
                self._broadcast({**self._state(),"type":"game_end","winner":self.active_players[0],"msg":msg})
                return
            self.current_player = next_p
            self._broadcast({**self._state(),"type":"state_update","msg":msg,"color":RED_B})
            self._start_timer(); return
        self.current_player = self._next()
        self._broadcast({**self._state(),"type":"state_update","msg":msg,"color":col})
        self._start_timer()

    def _do_donate(self, pnum, raw):
        parts = raw.split()
        if len(parts) != 3:
            self._send_to(pnum,{"type":"msg","text":"Usage: /donate <pts> <player>","color":RED}); return
        try: amt, target = int(parts[1]), int(parts[2])
        except ValueError:
            self._send_to(pnum,{"type":"msg","text":"Usage: /donate <pts> <player>","color":RED}); return
        if amt <= 0 or target < 1 or target > self.num_players or target == pnum:
            self._send_to(pnum,{"type":"msg","text":"Invalid target.","color":RED}); return
        if target not in self.active_players:
            self._send_to(pnum,{"type":"msg","text":f"Player {target} is already out.","color":RED}); return
        actual = min(amt, self.scores[pnum-1])
        self.scores[pnum-1] -= actual; self.scores[target-1] += actual
        self.current_player = self._next()
        self._broadcast({**self._state(),"type":"state_update",
                         "msg":f"Player {pnum} donated {actual} pts to Player {target}.","color":ACCENT})
        self._start_timer()

    def _next(self):
        idx = self.active_players.index(self.current_player)
        return self.active_players[(idx+1) % len(self.active_players)]

    def _start_timer(self):
        self._timer_gen += 1; gen = self._timer_gen
        self.time_left = 30
        threading.Thread(target=self._timer_loop, args=(gen,), daemon=True).start()

    def _stop_timer(self): self._timer_gen += 1

    def _timer_loop(self, gen):
        import time
        while True:
            if self._timer_gen != gen: return
            self._broadcast({"type":"tick","time_left":self.time_left})
            if self.time_left == 0:
                if self._timer_gen == gen:
                    self._timer_gen += 1
                    with self.lock: self._do_skip(self.current_player)
                return
            time.sleep(1); self.time_left -= 1

    def _state(self):
        return {"current_player":self.current_player,"previous_word":self.previous_word,
                "wordlist":self.wordlist[:],"scores":self.scores[:],
                "active_players":self.active_players[:],"forbidden":self.forbidden,
                "num_players":self.num_players}

    def _broadcast(self, msg):
        for conn in self.clients.values():
            try: send_msg(conn, msg)
            except Exception: pass

    def _send_to(self, pnum, msg):
        try: send_msg(self.clients[pnum], msg)
        except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
#  GAME CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class GameClient:
    def __init__(self, on_message, on_disconnect=None):
        self.on_message = on_message; self.on_disconnect = on_disconnect; self.sock = None

    def connect(self, host, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def send_action(self, word):
        try: send_msg(self.sock, {"type":"action","word":word})
        except Exception: pass

    def _recv_loop(self):
        while True:
            msg = recv_msg(self.sock)
            if msg is None:
                if self.on_disconnect: self.on_disconnect()
                break
            self.on_message(msg)


# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════

class ShiritoriApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shiritori")
        self.geometry("760x660")
        self.resizable(True, True)
        self.minsize(640, 540)
        self.configure(fg_color=BG)
        self._fs = False
        self.bind("<F11>", lambda e: self._toggle_fs())
        self.bind("<Escape>", lambda e: self._exit_fs())
        self.server = None; self.client = None; self.player_num = None
        self.g_current = 1; self.g_prev_word = "apple"; self.g_wordlist = []
        self.g_scores = []; self.g_active = []; self.g_forbidden = "?"; self.g_nplayers = 2
        self._game_active = False
        self._show_lobby()

    def _toggle_fs(self):
        self._fs = not self._fs; self.attributes("-fullscreen", self._fs)

    def _exit_fs(self):
        if self._fs: self._fs = False; self.attributes("-fullscreen", False)

    def _clear(self):
        self._game_active = False
        if hasattr(self, "l_timer_id") and self.l_timer_id:
            self.after_cancel(self.l_timer_id); self.l_timer_id = None
        for w in self.winfo_children(): w.destroy()

    def _set_msg(self, text, color):
        if hasattr(self, "_msg_lbl") and self._msg_lbl.winfo_exists():
            self._msg_lbl.configure(text=text, text_color=color)

    # ── lobby ─────────────────────────────────────────────────────────────────
    def _show_lobby(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=64, pady=44)

        # title
        title_frame = ctk.CTkFrame(root, fg_color="transparent")
        title_frame.pack(pady=(0, 6))
        _lbl(title_frame, "✦  SHIRITORI  ✦", size=34, weight="bold", color=ACCENT).pack()
        _lbl(root, "chain words · survive · dominate", size=12, color=DIM).pack(pady=(0, 30))

        # local card
        lc = _card(root)
        lc.pack(fill="x", pady=(0, 10))
        lh = ctk.CTkFrame(lc, fg_color="transparent")
        lh.pack(fill="x", padx=20, pady=(16, 6))
        _lbl(lh, "Local Play", size=14, weight="bold", color=TEXT).pack(side="left")
        _lbl(lh, "same PC", size=11, color=DIM).pack(side="right")
        _lbl(lc, "All players share this computer, passing it around each turn.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(0, 12))
        _btn_solid(lc, "Play Local", self._show_local_setup, height=40).pack(
            fill="x", padx=16, pady=(0, 16))

        # network card
        nc = _card(root)
        nc.pack(fill="x", pady=(0, 10))
        nh = ctk.CTkFrame(nc, fg_color="transparent")
        nh.pack(fill="x", padx=20, pady=(16, 6))
        _lbl(nh, "Network Play", size=14, weight="bold", color=TEXT).pack(side="left")
        _lbl(nh, "LAN", size=11, color=DIM).pack(side="right")
        _lbl(nc, "Each player connects from their own PC on the same network.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(0, 12))
        br = ctk.CTkFrame(nc, fg_color="transparent")
        br.pack(fill="x", padx=16, pady=(0, 16))
        _btn_solid(br, "Host", self._show_host_setup, height=40).pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        _btn(br, "Join", self._show_join, height=40).pack(
            side="left", fill="x", expand=True)

        _lbl(root, "F11 — fullscreen", size=11, color=DIM).pack(pady=(10, 0))

    # ── local setup ───────────────────────────────────────────────────────────
    def _show_local_setup(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=80, pady=52)
        _lbl(root, "Local Game", size=24, weight="bold", color=ACCENT).pack(pady=(0, 24))

        card = _card(root)
        card.pack(fill="x", pady=(0, 20))
        _lbl(card, "Number of players", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(16, 8))
        self._lpvar = ctk.IntVar(value=2)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))
        self._lslbl = _lbl(row, "2 players", size=13, weight="bold", color=GLOW, width=90)
        ctk.CTkSlider(row, from_=2, to=8, number_of_steps=6, variable=self._lpvar,
                      progress_color=ACCENT, button_color=GLOW,
                      command=lambda v: self._lslbl.configure(
                          text=f"{int(v)} players"),
                      ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._lslbl.pack(side="left")

        _btn_solid(root, "Start Game", self._start_local_game, height=46).pack(
            fill="x", pady=(0, 10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=36).pack(fill="x")

    def _start_local_game(self):
        n = int(self._lpvar.get())
        self.l_nplayers = n; self.l_scores = [0] * n
        self.l_active = list(range(1, n + 1)); self.l_wordlist = ["apple"]
        self.l_forbidden = chr(random.randint(ord("a"), ord("z")))
        self.l_current = 1; self.l_prevword = "apple"; self.notepad = []
        self.l_timer_id = None
        self._show_local_game()

    # ── local game ────────────────────────────────────────────────────────────
    def _show_local_game(self):
        self._clear(); self._game_active = True
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # header card
        hdr = _card(left)
        hdr.pack(fill="x", pady=(0, 8))
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 0))

        wc = ctk.CTkFrame(top, fg_color="transparent")
        wc.pack(side="left", fill="x", expand=True)
        self._l_turn_lbl = _lbl(wc, "", size=11, color=DIM)
        self._l_turn_lbl.pack(anchor="w")
        self._l_word_lbl = _lbl(wc, "", size=30, weight="bold", color=GLOW)
        self._l_word_lbl.pack(anchor="w", pady=(4, 0))

        badges = ctk.CTkFrame(top, fg_color="transparent")
        badges.pack(side="right")

        tb = _card2(badges, border_color=BORDER_A)
        tb.pack(side="left", padx=(0, 8))
        _lbl(tb, "time", size=10, color=ACCENT).pack(padx=12, pady=(6, 0))
        self._l_timer_lbl = _lbl(tb, "30", size=22, weight="bold", color=ACCENT)
        self._l_timer_lbl.pack(padx=12, pady=(0, 6))

        fb = _card2(badges, border_color="#7C2D2D")
        fb.pack(side="left")
        _lbl(fb, "forbidden", size=10, color=RED).pack(padx=12, pady=(6, 0))
        self._l_forb_lbl = _lbl(fb, self.l_forbidden.upper(), size=22, weight="bold", color=RED)
        self._l_forb_lbl.pack(padx=12, pady=(0, 6))

        self._l_hint_lbl = _lbl(hdr, "", size=11, color=DIM)
        self._l_hint_lbl.pack(anchor="w", padx=18, pady=(6, 14))

        # input card
        inp = _card(left)
        inp.pack(fill="x", pady=(0, 8))
        self._l_entry = _entry(inp, "Type your word and press Enter…")
        self._l_entry.pack(fill="x", padx=14, pady=(14, 8))
        self._l_entry.bind("<Return>", lambda e: self._local_submit())
        _btn_solid(inp, "Play Word", self._local_submit, height=40).pack(
            fill="x", padx=14, pady=(0, 8))
        self._msg_lbl = _lbl(inp, "", size=11, color=DIM, wraplength=380)
        self._msg_lbl.pack(padx=14, pady=(0, 12))

        # chain card
        chain = _card(left)
        chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent")
        cr.pack(fill="x", padx=14, pady=(10, 4))
        _lbl(cr, "Word chain", size=11, color=DIM).pack(side="left")
        self._l_chain_cnt = _lbl(cr, "1", size=12, weight="bold", color=ACCENT)
        self._l_chain_cnt.pack(side="right")
        self._l_chain_box = ctk.CTkTextbox(
            chain, font=_F(12), fg_color=CARD2,
            activate_scrollbars=True, wrap="word", text_color=TEXT,
            corner_radius=8)
        self._l_chain_box.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._l_chain_box.configure(state="disabled")

        # right panel
        right = _card(outer)
        right.configure(width=210)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        _lbl(right, "Scores", size=13, weight="bold", color=GLOW).pack(padx=14, pady=(16, 8))
        self._l_sc_cards = {}; self._l_sc_pts = {}; self._l_sc_names = {}
        for i in range(1, self.l_nplayers + 1):
            f = _card2(right, border_color=BORDER)
            f.pack(fill="x", padx=8, pady=2)
            n = _lbl(f, f"Player {i}", size=11, color=TEXT)
            n.pack(side="left", padx=(10, 4), pady=6)
            p = _lbl(f, "0", size=12, weight="bold", color=ACCENT)
            p.pack(side="right", padx=10)
            self._l_sc_cards[i] = f; self._l_sc_pts[i] = p; self._l_sc_names[i] = n

        _divider(right)
        _lbl(right, "Notepad", size=11, color=DIM).pack(padx=12)
        self._l_notepad_box = ctk.CTkTextbox(
            right, font=_F(11), fg_color=CARD2,
            activate_scrollbars=True, wrap="word",
            height=70, text_color=TEXT, corner_radius=8)
        self._l_notepad_box.pack(fill="x", padx=8, pady=(4, 4))
        self._l_notepad_box.configure(state="disabled")
        self._l_notepad_entry = _entry(right, "word → Enter to save", height=30)
        self._l_notepad_entry.pack(fill="x", padx=8, pady=(0, 2))
        self._l_notepad_entry.bind("<Return>", lambda e: self._l_notepad_enter())
        self._l_notepad_msg = _lbl(right, "", size=10, color=DIM)
        self._l_notepad_msg.pack(padx=8, pady=(0, 4))

        _divider(right)
        _lbl(right, "commands", size=10, color=DIM).pack()
        for cmd in ["/skip", "/donate <pts> <p>", "/wordlist", "/help"]:
            _lbl(right, cmd, size=10, color=ACCENT).pack(pady=1)
        _divider(right)
        _btn(right, "⛶  Fullscreen", self._toggle_fs, color=DIM, size=10,
             height=26).pack(fill="x", padx=8, pady=(0, 10))

        self._l_entry.focus()
        self._local_update_ui(); self._l_start_timer()

    def _local_update_ui(self):
        w, last = self.l_prevword, self.l_prevword[-1]
        self._l_turn_lbl.configure(text=f"Player {self.l_current}'s turn")
        self._l_word_lbl.configure(text=w)
        self._l_hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._l_forb_lbl.configure(text=self.l_forbidden.upper())
        self._l_chain_box.configure(state="normal")
        self._l_chain_box.delete("1.0", "end")
        self._l_chain_box.insert("end", "  →  ".join(self.l_wordlist))
        self._l_chain_box.configure(state="disabled")
        self._l_chain_cnt.configure(text=str(len(self.l_wordlist)))
        for i in range(1, self.l_nplayers + 1):
            out = i not in self.l_active; active = i == self.l_current and not out
            self._l_sc_pts[i].configure(text=str(self.l_scores[i - 1]))
            if out:
                self._l_sc_cards[i].configure(border_color="#3D0000")
                self._l_sc_pts[i].configure(text_color=RED_B)
                self._l_sc_names[i].configure(text_color=DIM)
            elif active:
                self._l_sc_cards[i].configure(border_color=ACCENT)
                self._l_sc_pts[i].configure(text_color=GLOW)
                self._l_sc_names[i].configure(text_color=TEXT)
            else:
                self._l_sc_cards[i].configure(border_color=BORDER)
                self._l_sc_pts[i].configure(text_color=DIM)
                self._l_sc_names[i].configure(text_color=DIM)

    def _l_set_msg(self, text, color): self._msg_lbl.configure(text=text, text_color=color)

    def _l_next(self):
        idx = self.l_active.index(self.l_current)
        return self.l_active[(idx + 1) % len(self.l_active)]

    def _l_start_timer(self):
        if hasattr(self, "l_timer_id") and self.l_timer_id:
            self.after_cancel(self.l_timer_id)
        self.l_time_left = 30; self._l_tick()

    def _l_tick(self):
        if not self._game_active: return
        t = self.l_time_left
        if hasattr(self, "_l_timer_lbl") and self._l_timer_lbl.winfo_exists():
            self._l_timer_lbl.configure(text=str(t), text_color=RED_B if t <= 10 else ACCENT)
        if t <= 0: self._l_timer_expired(); return
        self.l_time_left -= 1; self.l_timer_id = self.after(1000, self._l_tick)

    def _l_timer_expired(self):
        p = self.l_current; o = random.randint(0, 2)
        if o == 0:
            self.l_scores[p - 1] = max(0, self.l_scores[p - 1] - 10)
            self._l_set_msg(f"Time! Player {p} loses 10 pts.", ORANGE)
        elif o == 1:
            self._l_set_msg(f"Time! Player {p} safe skip.", GREEN)
        else:
            next_p = self._l_next(); self.l_active.remove(p)
            self._l_set_msg(f"Time! Player {p} eliminated!", RED_B)
            self._local_update_ui()
            if len(self.l_active) == 1:
                if self.l_timer_id: self.after_cancel(self.l_timer_id)
                self.after(1400, lambda: self._local_end(self.l_active[0])); return
            self.l_current = next_p; self.after(1000, self._local_update_ui)
            self._l_start_timer(); return
        self.l_current = self._l_next(); self._local_update_ui(); self._l_start_timer()

    def _l_notepad_enter(self):
        raw = self._l_notepad_entry.get().strip().lower()
        self._l_notepad_entry.delete(0, "end")
        if not raw: self._l_notepad_entry.focus(); return
        if dictionary and raw not in dictionary:
            self._l_notepad_msg.configure(text=f'"{raw}" — not a word', text_color=RED)
            self.after(1500, lambda: self._l_notepad_msg.configure(text=""))
            self._l_notepad_entry.focus(); return
        self.notepad.append(raw)
        self._l_notepad_msg.configure(text=f'"{raw}" saved ✓', text_color=GREEN)
        self.after(1200, lambda: self._l_notepad_msg.configure(text=""))
        self._l_notepad_box.configure(state="normal")
        self._l_notepad_box.delete("1.0", "end")
        self._l_notepad_box.insert("end", "\n".join(self.notepad))
        self._l_notepad_box.configure(state="disabled")
        self._l_notepad_entry.focus()

    def _local_submit(self):
        raw = self._l_entry.get().strip().lower(); self._l_entry.delete(0, "end")
        if not raw: return
        p = self.l_current
        if raw == "/help":
            self._l_set_msg("/skip · /donate <pts> <p> · /wordlist · /help", ACCENT); return
        if raw == "/rules":
            self._l_set_msg(f"Chain by last letter. No repeats. Forbidden: '{self.l_forbidden}'.", ACCENT); return
        if raw == "/wordlist":
            self._l_set_msg("Used: " + ", ".join(self.l_wordlist), ACCENT); return
        if raw == "/skip":
            o = random.randint(0, 2)
            if o == 0:
                self.l_scores[p - 1] = max(0, self.l_scores[p - 1] - 10)
                self._l_set_msg(f"Player {p} skipped — lost 10 pts.", ORANGE)
            elif o == 1:
                self._l_set_msg(f"Player {p} skipped safely.", GREEN)
            else:
                next_p = self._l_next(); self.l_active.remove(p)
                self._l_set_msg(f"Player {p} skipped and got eliminated!", RED_B)
                self._local_update_ui()
                if len(self.l_active) == 1:
                    if self.l_timer_id: self.after_cancel(self.l_timer_id)
                    self.after(1200, lambda: self._local_end(self.l_active[0])); return
                self.l_current = next_p; self.after(1000, self._local_update_ui)
                self._l_start_timer(); return
            self.l_current = self._l_next(); self._local_update_ui(); self._l_start_timer(); return
        if raw.startswith("/donate"):
            parts = raw.split()
            if len(parts) != 3: self._l_set_msg("/donate <pts> <player>", RED); return
            try: amt, target = int(parts[1]), int(parts[2])
            except: self._l_set_msg("/donate <pts> <player>", RED); return
            if amt <= 0 or target < 1 or target > self.l_nplayers or target == p:
                self._l_set_msg("Invalid target.", RED); return
            if target not in self.l_active: self._l_set_msg(f"Player {target} is already out.", RED); return
            actual = min(amt, self.l_scores[p - 1])
            self.l_scores[p - 1] -= actual; self.l_scores[target - 1] += actual
            self._l_set_msg(f"Player {p} donated {actual} pts to Player {target}.", ACCENT)
            self.l_current = self._l_next(); self._local_update_ui(); self._l_start_timer(); return
        if raw in self.l_wordlist: self._l_set_msg("Already used — pick a different word.", RED); return
        if dictionary and raw not in dictionary:
            self._l_set_msg(f'"{raw}" is not a valid English word.', RED); return
        if raw[0] != self.l_prevword[-1]:
            self._l_set_msg(f'Word must start with "{self.l_prevword[-1]}".', RED); return
        if raw[-1] == self.l_forbidden:
            next_p = self._l_next(); self.l_active.remove(p)
            self._l_set_msg(f"Player {p} is out! Forbidden letter '{self.l_forbidden}'.", RED_B)
            self._local_update_ui()
            if len(self.l_active) == 1:
                if self.l_timer_id: self.after_cancel(self.l_timer_id)
                self.after(1400, lambda: self._local_end(self.l_active[0])); return
            self.l_current = next_p; self.after(1000, self._local_update_ui)
            self._l_start_timer(); return
        self.l_wordlist.append(raw); self.l_scores[p - 1] += len(raw)
        self.l_prevword = raw; self._l_set_msg(f"+{len(raw)} pts for Player {p}.", GREEN)
        self.l_current = self._l_next(); self._local_update_ui(); self._l_start_timer()

    def _local_end(self, winner):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=60, pady=36)
        _lbl(root, "✦", size=48, color=ACCENT).pack(pady=(0, 4))
        _lbl(root, "Game Over", size=26, weight="bold").pack()
        _lbl(root, f"Player {winner} wins!", size=15, weight="bold", color=GLOW).pack(pady=(4, 20))
        card = _card(root); card.pack(fill="x", pady=(0, 16))
        _lbl(card, "Final Scores", size=12, color=DIM).pack(anchor="w", padx=20, pady=(14, 6))
        for i in sorted(range(1, self.l_nplayers + 1),
                        key=lambda x: self.l_scores[x - 1], reverse=True):
            out = i not in self.l_active; is_w = i == winner
            row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(fill="x", padx=14, pady=3)
            col = GLOW if is_w else (RED_B if out else DIM)
            _lbl(row, f"Player {i}" + (" · out" if out else "") + (" 🏆" if is_w else ""),
                 size=12, weight="bold" if is_w else "normal", color=col).pack(side="left")
            _lbl(row, f"{self.l_scores[i-1]} pts", size=12, color=col).pack(side="right")
        _lbl(card, f"Words played: {len(self.l_wordlist)}", size=11, color=DIM).pack(
            anchor="w", padx=20, pady=(4, 14))
        _btn_solid(root, "Play Again", self._show_lobby, height=46).pack(fill="x")

    # ── host setup ────────────────────────────────────────────────────────────
    def _show_host_setup(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=80, pady=52)
        _lbl(root, "Host a Game", size=24, weight="bold", color=ACCENT).pack(pady=(0, 24))
        card = _card(root); card.pack(fill="x", pady=(0, 20))
        _lbl(card, "Number of players", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(16, 8))
        self._pvar = ctk.IntVar(value=2)
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(fill="x", padx=20, pady=(0, 16))
        self._slbl = _lbl(row, "2 players", size=13, weight="bold", color=GLOW, width=90)
        ctk.CTkSlider(row, from_=2, to=8, number_of_steps=6, variable=self._pvar,
                      progress_color=ACCENT, button_color=GLOW,
                      command=lambda v: self._slbl.configure(text=f"{int(v)} players"),
                      ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._slbl.pack(side="left")
        _btn_solid(root, "Create Lobby", self._create_lobby, height=46).pack(fill="x", pady=(0, 10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=36).pack(fill="x")

    def _create_lobby(self):
        n = int(self._pvar.get())
        self.server = GameServer(n, lambda msg: self.after(0, self._on_server_event, msg))
        self.server.listen()
        self._show_waiting_room(is_host=True, total=n)
        threading.Thread(target=self._host_connect, daemon=True).start()

    def _host_connect(self):
        import time; time.sleep(0.25)
        self.client = GameClient(lambda msg: self.after(0, self._on_client_msg, msg),
                                 on_disconnect=lambda: self.after(0, self._on_disconnect))
        try: self.client.connect("127.0.0.1")
        except Exception as e: self.after(0, lambda: self._set_msg(f"Error: {e}", RED))

    def _on_server_event(self, msg):
        if msg["type"] == "player_joined" and hasattr(self, "_conn_lbl"):
            if self._conn_lbl.winfo_exists():
                self._conn_lbl.configure(
                    text=f"{msg['count']}/{self.server.num_players} connected")

    def _on_disconnect(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=80, pady=80)
        _lbl(root, "✦", size=40, color=RED).pack(pady=(0, 8))
        _lbl(root, "Disconnected", size=20, weight="bold", color=RED_B).pack(pady=(0, 8))
        _lbl(root, "Connection to host was lost.", size=12, color=DIM).pack(pady=(0, 28))
        _btn_solid(root, "← Back to Lobby", self._show_lobby, height=44).pack(fill="x")

    # ── join ──────────────────────────────────────────────────────────────────
    def _show_join(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=80, pady=52)
        _lbl(root, "Join a Game", size=24, weight="bold", color=ACCENT).pack(pady=(0, 24))
        card = _card(root); card.pack(fill="x", pady=(0, 20))
        _lbl(card, "Host IP address", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(16, 8))
        self._ip_entry = _entry(card, "192.168.X.XX", height=44)
        self._ip_entry.pack(fill="x", padx=20, pady=(0, 12))
        self._ip_entry.bind("<Return>", lambda e: self._do_join())
        history = load_ip_history()
        if history:
            _lbl(card, "Recent", size=11, color=DIM).pack(anchor="w", padx=20, pady=(0, 4))
            self._ip_dropdown = ctk.CTkOptionMenu(
                card, values=history, font=_F(12), height=36, corner_radius=10,
                fg_color=CARD2, button_color=BORDER_A, button_hover_color="#5B21B6",
                dropdown_fg_color=CARD, dropdown_hover_color="#1E1035",
                text_color=TEXT, dropdown_text_color=TEXT,
                command=self._on_ip_selected)
            self._ip_dropdown.pack(fill="x", padx=20, pady=(0, 6))
            self._ip_dropdown.set("Select recent IP…")
            _btn(card, "Clear history", self._clear_ip_history, color=DIM,
                 size=11, height=26).pack(anchor="e", padx=20, pady=(0, 12))
        else:
            ctk.CTkFrame(card, height=1, fg_color="transparent").pack(pady=8)
        self._msg_lbl = _lbl(root, "", size=11, color=DIM); self._msg_lbl.pack(pady=(0, 8))
        _btn_solid(root, "Connect", self._do_join, height=46).pack(fill="x", pady=(0, 10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=36).pack(fill="x")
        self._ip_entry.focus()

    def _on_ip_selected(self, val):
        self._ip_entry.delete(0, "end"); self._ip_entry.insert(0, val)

    def _clear_ip_history(self):
        save_config({k: v for k, v in load_config().items() if k != "ip_history"})
        self._show_join()

    def _do_join(self):
        ip = self._ip_entry.get().strip()
        if not ip: self._set_msg("Please enter an IP.", RED); return
        self._set_msg("Connecting…", ACCENT)
        save_ip_to_history(ip)
        self.client = GameClient(lambda msg: self.after(0, self._on_client_msg, msg),
                                 on_disconnect=lambda: self.after(0, self._on_disconnect))
        threading.Thread(target=self._try_connect, args=(ip,), daemon=True).start()

    def _try_connect(self, ip):
        try: self.client.connect(ip)
        except Exception as e: self.after(0, lambda: self._set_msg(f"Failed: {e}", RED))

    # ── waiting room ──────────────────────────────────────────────────────────
    def _show_waiting_room(self, is_host=False, total=None):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=80, pady=52)
        _lbl(root, "Lobby", size=24, weight="bold", color=ACCENT).pack(pady=(0, 8))
        _lbl(root, "Waiting for players…", size=12, color=DIM).pack(pady=(0, 24))
        if is_host:
            ip = get_local_ip()
            card = _card(root); card.pack(fill="x", pady=(0, 20))
            _lbl(card, "Your IP  — share with players", size=11, color=DIM).pack(
                anchor="w", padx=20, pady=(16, 8))
            ibox = ctk.CTkFrame(card, fg_color=CARD2, corner_radius=10)
            ibox.pack(fill="x", padx=20, pady=(0, 8))
            _lbl(ibox, ip, size=22, weight="bold", color=GLOW).pack(padx=16, pady=14)
            _lbl(card, f"Port: {PORT}", size=11, color=DIM).pack(
                anchor="w", padx=20, pady=(0, 14))
        t = f"0/{total} connected" if is_host else "Connecting…"
        self._conn_lbl = _lbl(root, t, size=13, color=ACCENT)
        self._conn_lbl.pack(pady=8)
        self._msg_lbl = _lbl(root, "Game starts when all players join.", size=11, color=DIM)
        self._msg_lbl.pack()

    # ── client message router ─────────────────────────────────────────────────
    def _on_client_msg(self, msg):
        t = msg.get("type")
        if t == "welcome":
            self.player_num = msg["player_num"]; self.g_nplayers = msg["num_players"]
            if not hasattr(self, "_conn_lbl") or not self._conn_lbl.winfo_exists():
                self._show_waiting_room()
            if self._conn_lbl.winfo_exists():
                self._conn_lbl.configure(
                    text=f"You are Player {self.player_num} — waiting…")
        elif t == "tick":
            tv = msg.get("time_left", 30)
            if hasattr(self, "_g_timer_lbl") and self._g_timer_lbl.winfo_exists():
                self._g_timer_lbl.configure(
                    text=str(tv), text_color=RED_B if tv <= 10 else ACCENT)
        elif t == "game_start":
            self._apply_state(msg); self._show_game()
        elif t == "state_update":
            self._apply_state(msg)
            if self._game_active:
                self._update_ui()
                if msg.get("msg"): self._set_msg(msg["msg"], msg.get("color", ACCENT))
        elif t == "msg":
            self._set_msg(msg["text"], msg["color"])
        elif t == "game_end":
            self._apply_state(msg); self._show_end(msg["winner"], msg.get("msg", ""))

    def _apply_state(self, msg):
        self.g_current = msg.get("current_player", 1)
        self.g_prev_word = msg.get("previous_word", "apple")
        self.g_wordlist = msg.get("wordlist", [])
        self.g_scores = msg.get("scores", [])
        self.g_active = msg.get("active_players", [])
        self.g_forbidden = msg.get("forbidden", "?")
        self.g_nplayers = msg.get("num_players", self.g_nplayers)

    # ── network game screen ───────────────────────────────────────────────────
    def _show_game(self):
        self._clear(); self._game_active = True; self.g_notepad = []
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        hdr = _card(left)
        hdr.pack(fill="x", pady=(0, 8))
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 0))

        wc = ctk.CTkFrame(top, fg_color="transparent")
        wc.pack(side="left", fill="x", expand=True)
        self._turn_lbl = _lbl(wc, "", size=11, color=DIM)
        self._turn_lbl.pack(anchor="w")
        _lbl(wc, f"✦  You are Player {self.player_num}", size=11, color=ACCENT).pack(anchor="w")
        self._word_lbl = _lbl(wc, "", size=30, weight="bold", color=GLOW)
        self._word_lbl.pack(anchor="w", pady=(4, 0))

        badges = ctk.CTkFrame(top, fg_color="transparent")
        badges.pack(side="right")

        tb = _card2(badges, border_color=BORDER_A)
        tb.pack(side="left", padx=(0, 8))
        _lbl(tb, "time", size=10, color=ACCENT).pack(padx=12, pady=(6, 0))
        self._g_timer_lbl = _lbl(tb, "30", size=22, weight="bold", color=ACCENT)
        self._g_timer_lbl.pack(padx=12, pady=(0, 6))

        fb = _card2(badges, border_color="#7C2D2D")
        fb.pack(side="left")
        _lbl(fb, "forbidden", size=10, color=RED).pack(padx=12, pady=(6, 0))
        self._forb_lbl = _lbl(fb, "?", size=22, weight="bold", color=RED)
        self._forb_lbl.pack(padx=12, pady=(0, 6))

        self._hint_lbl = _lbl(hdr, "", size=11, color=DIM)
        self._hint_lbl.pack(anchor="w", padx=18, pady=(6, 14))

        inp = _card(left); inp.pack(fill="x", pady=(0, 8))
        self._entry = _entry(inp, "Type your word and press Enter…")
        self._entry.pack(fill="x", padx=14, pady=(14, 8))
        self._entry.bind("<Return>", lambda e: self._submit())
        self._play_btn = _btn_solid(inp, "Play Word", self._submit, height=40)
        self._play_btn.pack(fill="x", padx=14, pady=(0, 8))
        self._msg_lbl = _lbl(inp, "", size=11, color=DIM, wraplength=380)
        self._msg_lbl.pack(padx=14, pady=(0, 12))

        chain = _card(left); chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent")
        cr.pack(fill="x", padx=14, pady=(10, 4))
        _lbl(cr, "Word chain", size=11, color=DIM).pack(side="left")
        self._chain_cnt = _lbl(cr, "0", size=12, weight="bold", color=ACCENT)
        self._chain_cnt.pack(side="right")
        self._chain_box = ctk.CTkTextbox(
            chain, font=_F(12), fg_color=CARD2,
            activate_scrollbars=True, wrap="word", text_color=TEXT, corner_radius=8)
        self._chain_box.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._chain_box.configure(state="disabled")

        right = _card(outer)
        right.configure(width=210)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        _lbl(right, "Scores", size=13, weight="bold", color=GLOW).pack(padx=14, pady=(16, 8))
        self._sc_cards = {}; self._sc_pts = {}; self._sc_names = {}
        for i in range(1, self.g_nplayers + 1):
            f = _card2(right, border_color=BORDER)
            f.pack(fill="x", padx=8, pady=2)
            you = " (you)" if i == self.player_num else ""
            n = _lbl(f, f"P{i}{you}", size=11, color=TEXT)
            n.pack(side="left", padx=(10, 4), pady=6)
            p = _lbl(f, "0", size=12, weight="bold", color=ACCENT)
            p.pack(side="right", padx=10)
            self._sc_cards[i] = f; self._sc_pts[i] = p; self._sc_names[i] = n

        _divider(right)
        _lbl(right, "Notepad", size=11, color=DIM).pack(padx=12)
        self._g_notepad_box = ctk.CTkTextbox(
            right, font=_F(11), fg_color=CARD2,
            activate_scrollbars=True, wrap="word",
            height=70, text_color=TEXT, corner_radius=8)
        self._g_notepad_box.pack(fill="x", padx=8, pady=(4, 4))
        self._g_notepad_box.configure(state="disabled")
        self._g_notepad_entry = _entry(right, "word → Enter to save", height=30)
        self._g_notepad_entry.pack(fill="x", padx=8, pady=(0, 2))
        self._g_notepad_entry.bind("<Return>", lambda e: self._g_notepad_enter())
        self._g_notepad_msg = _lbl(right, "", size=10, color=DIM)
        self._g_notepad_msg.pack(padx=8, pady=(0, 4))

        _divider(right)
        _lbl(right, "commands", size=10, color=DIM).pack()
        for cmd in ["/skip", "/donate <pts> <p>", "/wordlist", "/help"]:
            _lbl(right, cmd, size=10, color=ACCENT).pack(pady=1)
        _divider(right)
        _btn(right, "⛶  Fullscreen", self._toggle_fs, color=DIM, size=10,
             height=26).pack(fill="x", padx=8, pady=(0, 10))

        self._update_ui()

    def _update_ui(self):
        if not self.g_wordlist: return
        my_turn = self.g_current == self.player_num
        w, last = self.g_prev_word, self.g_prev_word[-1]
        self._turn_lbl.configure(
            text="✦ Your turn!" if my_turn else f"Player {self.g_current}'s turn")
        self._word_lbl.configure(text=w)
        self._hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._forb_lbl.configure(text=self.g_forbidden.upper())
        self._entry.configure(state="normal" if my_turn else "disabled")
        self._play_btn.configure(state="normal" if my_turn else "disabled")
        if my_turn: self._entry.focus()
        self._chain_box.configure(state="normal")
        self._chain_box.delete("1.0", "end")
        self._chain_box.insert("end", "  →  ".join(self.g_wordlist))
        self._chain_box.configure(state="disabled")
        self._chain_cnt.configure(text=str(len(self.g_wordlist)))
        for i in range(1, self.g_nplayers + 1):
            out = i not in self.g_active; active = i == self.g_current and not out
            score = self.g_scores[i - 1] if i <= len(self.g_scores) else 0
            self._sc_pts[i].configure(text=str(score))
            if out:
                self._sc_cards[i].configure(border_color="#3D0000")
                self._sc_pts[i].configure(text_color=RED_B)
                self._sc_names[i].configure(text_color=DIM)
            elif active:
                self._sc_cards[i].configure(border_color=ACCENT)
                self._sc_pts[i].configure(text_color=GLOW)
                self._sc_names[i].configure(text_color=TEXT)
            else:
                self._sc_cards[i].configure(border_color=BORDER)
                self._sc_pts[i].configure(text_color=DIM)
                self._sc_names[i].configure(text_color=DIM)

    def _g_notepad_enter(self):
        raw = self._g_notepad_entry.get().strip().lower()
        self._g_notepad_entry.delete(0, "end")
        if not raw: self._g_notepad_entry.focus(); return
        if dictionary and raw not in dictionary:
            self._g_notepad_msg.configure(text=f'"{raw}" — not a word', text_color=RED)
            self.after(1500, lambda: self._g_notepad_msg.configure(text=""))
            self._g_notepad_entry.focus(); return
        self.g_notepad.append(raw)
        self._g_notepad_msg.configure(text=f'"{raw}" saved ✓', text_color=GREEN)
        self.after(1200, lambda: self._g_notepad_msg.configure(text=""))
        self._g_notepad_box.configure(state="normal")
        self._g_notepad_box.delete("1.0", "end")
        self._g_notepad_box.insert("end", "\n".join(self.g_notepad))
        self._g_notepad_box.configure(state="disabled")
        self._g_notepad_entry.focus()

    def _submit(self):
        if self.g_current != self.player_num: return
        raw = self._entry.get().strip().lower(); self._entry.delete(0, "end")
        if not raw: return
        if raw == "/help":
            self._set_msg("/skip · /donate <pts> <p> · /wordlist · /help", ACCENT); return
        if raw == "/rules":
            self._set_msg(f"Chain by last letter. No repeats. Forbidden: '{self.g_forbidden}'.", ACCENT); return
        if raw == "/wordlist":
            self._set_msg("Used: " + ", ".join(self.g_wordlist), ACCENT); return
        self.client.send_action(raw)

    def _show_end(self, winner, extra=""):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=60, pady=36)
        is_me = winner == self.player_num
        _lbl(root, "✦", size=48, color=ACCENT if is_me else DIM).pack(pady=(0, 4))
        _lbl(root, "Game Over", size=26, weight="bold").pack()
        msg = f"Player {winner} wins!" + (" — that's you!" if is_me else "")
        _lbl(root, msg, size=15, weight="bold", color=GLOW if is_me else RED_B).pack(pady=(6, 4))
        if extra: _lbl(root, extra[:70], size=11, color=DIM).pack(pady=(0, 16))
        card = _card(root); card.pack(fill="x", pady=(8, 20))
        _lbl(card, "Final Scores", size=12, color=DIM).pack(anchor="w", padx=20, pady=(14, 6))
        for i in sorted(range(1, self.g_nplayers + 1),
                        key=lambda x: self.g_scores[x - 1], reverse=True):
            out = i not in self.g_active; is_w = i == winner
            you = " (you)" if i == self.player_num else ""
            row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(fill="x", padx=14, pady=3)
            col = GLOW if is_w else (RED_B if out else DIM)
            score = self.g_scores[i - 1] if i <= len(self.g_scores) else 0
            _lbl(row, f"Player {i}{you}" + (" · out" if out else "") + (" 🏆" if is_w else ""),
                 size=12, weight="bold" if is_w else "normal", color=col).pack(side="left")
            _lbl(row, f"{score} pts", size=12, color=col).pack(side="right")
        _lbl(card, f"Words played: {len(self.g_wordlist)}", size=11, color=DIM).pack(
            anchor="w", padx=20, pady=(4, 14))
        _btn_solid(root, "← Back to Lobby", self._show_lobby, height=46).pack(fill="x")


if __name__ == "__main__":
    app = ShiritoriApp()
    app.mainloop()