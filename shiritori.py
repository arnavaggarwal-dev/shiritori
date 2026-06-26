# ─────────────────────────────────────────────────────────────────────────────
#  Shiritori — All-in-One Edition  ✦ cosmic nebula theme
#  Modes: Bot  ·  Local pass-and-play  ·  Network (host / join)
#
#  pip install customtkinter
#
#  pyinstaller --onefile --windowed --icon=favicon.ico
#    --add-data "words_dictionary.json;."
#    --add-data "C:\path\to\customtkinter;customtkinter"
#    shiritori.py
# ─────────────────────────────────────────────────────────────────────────────

import customtkinter as ctk
import random, json, socket, threading, sys, os
from collections import defaultdict

PORT = 55731

# ── helpers ───────────────────────────────────────────────────────────────────
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

def load_ip_history(): return load_config().get("ip_history", [])

def save_ip_to_history(ip):
    cfg = load_config(); h = cfg.get("ip_history", [])
    if ip in h: h.remove(ip)
    h.insert(0, ip); cfg["ip_history"] = h[:10]; save_config(cfg)

# ── dictionary + bot AI ───────────────────────────────────────────────────────
try:
    with open(resource_path("words_dictionary.json")) as f:
        _dict_raw = list(json.load(f).keys())
    dictionary_set = set(_dict_raw)
except FileNotFoundError:
    _dict_raw = []; dictionary_set = set()

WORDS_BY_LETTER = defaultdict(list)
for _w in _dict_raw:
    WORDS_BY_LETTER[_w[0]].append(_w)

def bot_pick_word(start, wset, forbidden, difficulty):
    cands = [w for w in WORDS_BY_LETTER.get(start, []) if w not in wset and len(w) > 1]
    if not cands: return None
    safe   = [w for w in cands if w[-1] != forbidden]
    danger = [w for w in cands if w[-1] == forbidden]
    danger_n = round(len(danger) * (100 - difficulty) / 100)
    safe_n   = round(len(safe)   * difficulty / 100)
    pool = (random.sample(danger, min(danger_n, len(danger))) +
            random.sample(safe,   min(safe_n,   len(safe))))
    if not pool: pool = safe if safe else danger
    if danger and random.random() < 0.01: return random.choice(danger)
    return random.choice(pool)

def diff_label(d):
    if d <= 20:  return "easy"
    if d <= 40:  return "medium-easy"
    if d <= 60:  return "medium"
    if d <= 80:  return "hard"
    return             "expert"

# ── palette + theme ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG       = "#07050F"
CARD     = "#0D0818"
CARD2    = "#130E24"
BORDER   = "#2D1B54"
BORDER_A = "#6D28D9"
ACCENT   = "#A855F7"
GLOW     = "#C084FC"
RED      = "#F472B6"
RED_B    = "#EC4899"
GREEN    = "#34D399"
ORANGE   = "#FB923C"
DIM      = "#5B4D7A"
TEXT     = "#EDE9FE"

# ── UI helpers ────────────────────────────────────────────────────────────────
def _F(size, weight="normal"):
    return ctk.CTkFont(size=size, weight=weight)

def _card(parent, border_color=None, **kw):
    return ctk.CTkFrame(parent, corner_radius=16, fg_color=CARD,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _card2(parent, border_color=None, **kw):
    return ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD2,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _btn(parent, text, command, color=None, size=13, **kw):
    c = color or ACCENT
    return ctk.CTkButton(parent, text=text, font=_F(size, "bold"), command=command,
                         corner_radius=22, fg_color="transparent", hover_color=CARD2,
                         border_width=2, border_color=c, text_color=c, **kw)

def _btn_solid(parent, text, command, size=14, **kw):
    return ctk.CTkButton(parent, text=text, font=_F(size, "bold"), command=command,
                         corner_radius=22, fg_color="#7C3AED", hover_color="#9333EA",
                         text_color="#FFFFFF", **kw)

def _entry(parent, placeholder="", **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, font=_F(14),
                        corner_radius=14, fg_color=CARD2, border_color=BORDER_A,
                        border_width=1, text_color=TEXT,
                        placeholder_text_color=DIM, **kw)

def _lbl(parent, text, size=13, color=None, weight="normal", **kw):
    return ctk.CTkLabel(parent, text=text, font=_F(size, weight),
                        text_color=color or TEXT, **kw)

def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=BORDER, corner_radius=0).pack(
        fill="x", padx=14, pady=8)

def _slider(parent, var, from_, to, steps=None, command=None):
    kw = dict(variable=var, from_=from_, to=to,
              progress_color=ACCENT, button_color=GLOW,
              button_hover_color=ACCENT, height=18)
    if steps: kw["number_of_steps"] = steps
    if command: kw["command"] = command
    return ctk.CTkSlider(parent, **kw)

# ── networking ────────────────────────────────────────────────────────────────
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
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"

# ── game server ───────────────────────────────────────────────────────────────
class GameServer:
    def __init__(self, num_players, on_event):
        self.num_players = num_players; self.on_event = on_event
        self.clients = {}; self.lock = threading.Lock()
        self.scores = [0] * num_players
        self.active_players = list(range(1, num_players + 1))
        self.wordlist = ["apple"]; self.forbidden = chr(random.randint(ord("a"), ord("z")))
        self.current_player = 1; self.previous_word = "apple"; self._timer_gen = 0

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
                with self.lock: self._handle_disconnect(pnum); break
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
            self._send_to(pnum,{"type":"msg","text":"Already used.","color":RED}); return
        if dictionary_set and word not in dictionary_set:
            self._send_to(pnum,{"type":"msg","text":f'"{word}" — not a valid word.',"color":RED}); return
        if word[0] != self.previous_word[-1]:
            self._send_to(pnum,{"type":"msg","text":f'Must start with "{self.previous_word[-1]}".'}); return
        if word[-1] == self.forbidden:
            next_p = self._next(); self.active_players.remove(pnum)
            msg = f"Player {pnum} is out! Ended with forbidden '{self.forbidden}'."
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
        o = random.randint(0,2)
        if o == 0:
            self.scores[pnum-1] = max(0, self.scores[pnum-1]-10)
            msg, col = f"Player {pnum} skipped — lost 10 pts.", ORANGE
        elif o == 1:
            msg, col = f"Player {pnum} skipped safely.", GREEN
        else:
            next_p = self._next(); self.active_players.remove(pnum)
            msg = f"Player {pnum} skipped and was eliminated!"
            if len(self.active_players) == 1:
                self._stop_timer()
                self._broadcast({**self._state(),"type":"game_end","winner":self.active_players[0],"msg":msg}); return
            self.current_player = next_p
            self._broadcast({**self._state(),"type":"state_update","msg":msg,"color":RED_B})
            self._start_timer(); return
        self.current_player = self._next()
        self._broadcast({**self._state(),"type":"state_update","msg":msg,"color":col})
        self._start_timer()

    def _do_donate(self, pnum, raw):
        parts = raw.split()
        if len(parts) != 3:
            self._send_to(pnum,{"type":"msg","text":"/donate <pts> <player>","color":RED}); return
        try: amt, target = int(parts[1]), int(parts[2])
        except ValueError:
            self._send_to(pnum,{"type":"msg","text":"/donate <pts> <player>","color":RED}); return
        if amt<=0 or target<1 or target>self.num_players or target==pnum or target not in self.active_players:
            self._send_to(pnum,{"type":"msg","text":"Invalid target.","color":RED}); return
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
        self._timer_gen += 1; gen = self._timer_gen; self.time_left = 30
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

# ── game client ───────────────────────────────────────────────────────────────
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
#  RIGHT PANEL  (shared between bot + local + network game screens)
# ══════════════════════════════════════════════════════════════════════════════

def _build_right_panel(app, parent, n_players, bot_num=None, player_num=None,
                       show_bot_slider=False, show_commands=True, toggle_fs=None):
    """
    Returns (sc_cards, sc_pts, sc_names, notepad, notepad_box, notepad_entry, notepad_msg).
    Builds the right sidebar in the game layout.
    """
    right = _card(parent); right.configure(width=226)
    right.pack(side="right", fill="y"); right.pack_propagate(False)

    # ── scores ────────────────────────────────────────────────────────────────
    sh = ctk.CTkFrame(right, fg_color="transparent"); sh.pack(fill="x", padx=14, pady=(16,6))
    _lbl(sh, "Scores", size=14, weight="bold", color=GLOW).pack(side="left")

    sc_cards = {}; sc_pts = {}; sc_names = {}
    for i in range(1, n_players + 1):
        is_bot = (i == bot_num); is_me = (i == player_num)
        f = _card2(right, border_color=BORDER); f.pack(fill="x", padx=10, pady=2)
        if is_bot:   name = "🤖  Bot"
        elif is_me:  name = f"Player {i}  (you)"
        else:        name = f"Player {i}"
        nc = GLOW if is_bot else (ACCENT if is_me else DIM)
        n = _lbl(f, name, size=12, color=nc); n.pack(side="left", padx=(12,4), pady=8)
        p = _lbl(f, "0", size=13, weight="bold", color=ACCENT if not is_bot else GLOW)
        p.pack(side="right", padx=12)
        sc_cards[i] = f; sc_pts[i] = p; sc_names[i] = n

    # ── bot difficulty slider ─────────────────────────────────────────────────
    diff_badge = None; diff_desc = None; diff_slider = None
    if show_bot_slider:
        _divider(right)
        dh = ctk.CTkFrame(right, fg_color="transparent"); dh.pack(fill="x", padx=12)
        _lbl(dh, "🤖  Difficulty", size=12, weight="bold", color=GLOW).pack(side="left")
        diff_badge = _lbl(dh, str(app.bot_diff), size=12, weight="bold", color=GLOW)
        diff_badge.pack(side="right")
        app._diff_slider_var = ctk.IntVar(value=app.bot_diff)
        diff_slider = _slider(right, app._diff_slider_var, 1, 100, command=app._on_diff_change)
        diff_slider.pack(fill="x", padx=12, pady=(4,2))
        diff_desc = _lbl(right, diff_label(app.bot_diff), size=10, color=DIM)
        diff_desc.pack(padx=12, pady=(0,2))
        app._bot_play_lbl = _lbl(right, "", size=10, color=GLOW)
        app._bot_play_lbl.pack(padx=12, pady=(0,4))
        app._diff_badge = diff_badge; app._diff_desc = diff_desc

    # ── notepad ───────────────────────────────────────────────────────────────
    _divider(right)
    nph = ctk.CTkFrame(right, fg_color="transparent"); nph.pack(fill="x", padx=12)
    _lbl(nph, "Notepad", size=12, weight="bold").pack(side="left")
    _lbl(nph, "jot words", size=10, color=DIM).pack(side="right")
    notepad_box = ctk.CTkTextbox(right, font=_F(11), fg_color=CARD2,
                                  activate_scrollbars=True, wrap="word",
                                  height=80, text_color=TEXT, corner_radius=10)
    notepad_box.pack(fill="x", padx=10, pady=(4,4))
    notepad_box.configure(state="disabled")
    notepad_entry = _entry(right, "word → Enter to save", height=32)
    notepad_entry.pack(fill="x", padx=10, pady=(0,2))
    notepad_msg = _lbl(right, "", size=10, color=DIM)
    notepad_msg.pack(padx=10, pady=(0,4))

    # ── commands ──────────────────────────────────────────────────────────────
    if show_commands:
        _divider(right)
        _lbl(right, "commands", size=10, color=DIM).pack()
        for cmd in ["/skip", "/donate <pts> <p>", "/wordlist", "/help"]:
            _lbl(right, cmd, size=10, color=ACCENT).pack(pady=1)

    _divider(right)
    if toggle_fs:
        _btn(right, "⛶  Fullscreen", toggle_fs, color=DIM, size=10,
             height=28).pack(fill="x", padx=10, pady=(0,10))

    return sc_cards, sc_pts, sc_names, [], notepad_box, notepad_entry, notepad_msg


def _notepad_enter_fn(app_or_self, raw_getter, entry_widget, msg_lbl, box, store):
    raw = raw_getter().strip().lower(); entry_widget.delete(0,"end")
    if not raw: entry_widget.focus(); return
    if dictionary_set and raw not in dictionary_set:
        msg_lbl.configure(text=f'"{raw}" — not a word', text_color=RED)
        app_or_self.after(1500, lambda: msg_lbl.configure(text=""))
        entry_widget.focus(); return
    store.append(raw)
    msg_lbl.configure(text=f'"{raw}" saved ✓', text_color=GREEN)
    app_or_self.after(1200, lambda: msg_lbl.configure(text=""))
    box.configure(state="normal"); box.delete("1.0","end")
    box.insert("end", "\n".join(store)); box.configure(state="disabled")
    entry_widget.focus()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class ShiritoriApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shiritori")
        self.geometry("880x720")
        self.resizable(True, True)
        self.minsize(720, 580)
        self.configure(fg_color=BG)
        self._fs = False
        self._timer_id = None
        self._game_active = False
        self.server = None; self.client = None
        self.bind("<F11>",    lambda e: self._toggle_fs())
        self.bind("<Escape>", lambda e: self._exit_fs())
        self._show_lobby()

    # ── window helpers ────────────────────────────────────────────────────────
    def _toggle_fs(self):
        self._fs = not self._fs; self.attributes("-fullscreen", self._fs)

    def _exit_fs(self):
        if self._fs: self._fs = False; self.attributes("-fullscreen", False)

    def _clear(self):
        self._game_active = False
        if self._timer_id: self.after_cancel(self._timer_id); self._timer_id = None
        for w in self.winfo_children(): w.destroy()

    def _set_msg(self, text, color=DIM):
        if hasattr(self,"_msg_lbl") and self._msg_lbl.winfo_exists():
            self._msg_lbl.configure(text=text, text_color=color)

    # ══════════════════════════════════════════════════════════════════════════
    #  LOBBY
    # ══════════════════════════════════════════════════════════════════════════
    def _show_lobby(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=72, pady=48)

        _lbl(root, "✦  SHIRITORI  ✦", size=38, weight="bold", color=ACCENT).pack()
        _lbl(root, "chain words  ·  survive  ·  dominate",
             size=13, color=DIM).pack(pady=(4, 32))

        # Bot mode
        bc = _card(root, border_color=BORDER_A); bc.pack(fill="x", pady=(0,10))
        bh = ctk.CTkFrame(bc, fg_color="transparent"); bh.pack(fill="x", padx=20, pady=(18,6))
        _lbl(bh, "🤖  Bot Mode", size=15, weight="bold", color=GLOW).pack(side="left")
        _lbl(bh, "vs AI", size=11, color=DIM).pack(side="right")
        _lbl(bc, "Play against the bot. Adjust difficulty on the fly mid-game.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(0,14))
        _btn_solid(bc, "Play vs Bot", self._show_bot_setup, height=42).pack(
            fill="x", padx=18, pady=(0,18))

        # Local mode
        lc = _card(root); lc.pack(fill="x", pady=(0,10))
        lh = ctk.CTkFrame(lc, fg_color="transparent"); lh.pack(fill="x", padx=20, pady=(18,6))
        _lbl(lh, "🎮  Local Play", size=15, weight="bold").pack(side="left")
        _lbl(lh, "same PC", size=11, color=DIM).pack(side="right")
        _lbl(lc, "Pass the keyboard around — all players on this machine.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(0,14))
        _btn_solid(lc, "Play Local", self._show_local_setup, height=42).pack(
            fill="x", padx=18, pady=(0,18))

        # Network mode
        nc = _card(root); nc.pack(fill="x", pady=(0,10))
        nh = ctk.CTkFrame(nc, fg_color="transparent"); nh.pack(fill="x", padx=20, pady=(18,6))
        _lbl(nh, "🌐  Network Play", size=15, weight="bold").pack(side="left")
        _lbl(nh, "LAN", size=11, color=DIM).pack(side="right")
        _lbl(nc, "Each player connects from their own PC on the same network.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(0,14))
        nr = ctk.CTkFrame(nc, fg_color="transparent"); nr.pack(fill="x", padx=18, pady=(0,18))
        _btn_solid(nr, "Host", self._show_host_setup, height=42).pack(
            side="left", fill="x", expand=True, padx=(0,8))
        _btn(nr, "Join", self._show_join, height=42).pack(side="left", fill="x", expand=True)

        _lbl(root, "F11 — toggle fullscreen", size=11, color=DIM).pack(pady=(12,0))

    # ══════════════════════════════════════════════════════════════════════════
    #  BOT SETUP + GAME
    # ══════════════════════════════════════════════════════════════════════════
    def _show_bot_setup(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=56)

        _lbl(root, "Bot Mode", size=26, weight="bold", color=GLOW).pack(pady=(0,28))

        pc = _card(root); pc.pack(fill="x", pady=(0,10))
        _lbl(pc, "Human players", size=12, color=DIM).pack(anchor="w", padx=20, pady=(18,6))
        self._bpvar = ctk.IntVar(value=1)
        pr = ctk.CTkFrame(pc, fg_color="transparent"); pr.pack(fill="x", padx=20, pady=(0,6))
        self._bpslbl = _lbl(pr, "1 player", size=13, weight="bold", color=GLOW, width=90)
        _slider(pc, self._bpvar, 1, 7, steps=6,
                command=lambda v: self._bpslbl.configure(
                    text=f"{int(v)} player{'s' if int(v)>1 else ''}")).pack(
            fill="x", padx=20, pady=(0,4))
        self._bpslbl.pack(in_=pr, side="right")
        _lbl(pc, "The bot is always included as an extra.", size=11, color=DIM).pack(
            anchor="w", padx=20, pady=(0,16))

        dc = _card(root, border_color=BORDER_A); dc.pack(fill="x", pady=(0,10))
        dh = ctk.CTkFrame(dc, fg_color="transparent"); dh.pack(fill="x", padx=20, pady=(18,6))
        _lbl(dh, "Bot starting difficulty", size=12, weight="bold").pack(side="left")
        self._bdlbl = _lbl(dh, "50", size=13, weight="bold", color=GLOW)
        self._bdlbl.pack(side="right")
        self._bdvar = ctk.IntVar(value=50)
        _slider(dc, self._bdvar, 1, 100,
                command=lambda v: self._bdlbl.configure(text=str(int(v)))).pack(
            fill="x", padx=20, pady=(0,8))
        leg = ctk.CTkFrame(dc, fg_color=CARD2, corner_radius=10)
        leg.pack(fill="x", padx=20, pady=(0,18))
        lr = ctk.CTkFrame(leg, fg_color="transparent"); lr.pack(fill="x", padx=14, pady=8)
        for label, col in [("1  Easy", GREEN), ("50  Medium", ORANGE), ("100  Expert", RED_B)]:
            _lbl(lr, label, size=11, color=col).pack(side="left", expand=True)

        _btn_solid(root, "Start Game", self._start_bot_game, height=48).pack(fill="x", pady=(8,8))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=38).pack(fill="x")

    def _start_bot_game(self):
        n = int(self._bpvar.get())
        self.n_humans = n; self.n_players = n + 1; self.bot_num = n + 1
        self.scores = [0] * self.n_players; self.active = list(range(1, self.n_players + 1))
        self.wordlist = ["apple"]; self.wset = {"apple"}
        self.forbidden = chr(random.randint(ord("a"), ord("z")))
        self.current = 1; self.prevword = "apple"
        self.bot_diff = int(self._bdvar.get()); self.notepad = []
        self._show_bot_game()

    def _on_diff_change(self, val):
        self.bot_diff = int(val)
        if hasattr(self,"_diff_badge") and self._diff_badge.winfo_exists():
            self._diff_badge.configure(text=str(self.bot_diff))
        if hasattr(self,"_diff_desc") and self._diff_desc.winfo_exists():
            self._diff_desc.configure(text=diff_label(self.bot_diff))

    def _show_bot_game(self):
        self._clear(); self._game_active = True
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=14, pady=14)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        self._build_game_header(left, show_player_badge=False)
        self._build_input_card(left, submit_fn=self._bot_submit)

        chain = _card(left); chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent"); cr.pack(fill="x", padx=14, pady=(12,4))
        _lbl(cr, "Word chain", size=12, color=DIM).pack(side="left")
        self._chain_cnt = _lbl(cr, "1", size=13, weight="bold", color=ACCENT)
        self._chain_cnt.pack(side="right")
        self._chain_box = ctk.CTkTextbox(chain, font=_F(12), fg_color=CARD2,
                                          activate_scrollbars=True, wrap="word",
                                          text_color=TEXT, corner_radius=10)
        self._chain_box.pack(fill="both", expand=True, padx=14, pady=(0,12))
        self._chain_box.configure(state="disabled")

        sc_cards, sc_pts, sc_names, _, np_box, np_entry, np_msg = _build_right_panel(
            self, outer, self.n_players, bot_num=self.bot_num,
            show_bot_slider=True, show_commands=True, toggle_fs=self._toggle_fs)
        self._sc_cards = sc_cards; self._sc_pts = sc_pts; self._sc_names = sc_names
        self._np_box = np_box; self._np_entry = np_entry; self._np_msg = np_msg
        np_entry.bind("<Return>", lambda e: _notepad_enter_fn(
            self, np_entry.get, np_entry, np_msg, np_box, self.notepad))

        self._entry.focus(); self._update_ui(); self._start_timer()
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)

    def _build_game_header(self, parent, show_player_badge=False):
        hdr = _card(parent); hdr.pack(fill="x", pady=(0,10))
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(18,0))

        wc = ctk.CTkFrame(top, fg_color="transparent")
        wc.pack(side="left", fill="x", expand=True)
        self._turn_lbl = _lbl(wc, "", size=12, color=DIM); self._turn_lbl.pack(anchor="w")
        if show_player_badge:
            self._pnum_lbl = _lbl(wc, "", size=11, color=ACCENT)
            self._pnum_lbl.pack(anchor="w")
        self._word_lbl = _lbl(wc, "", size=34, weight="bold", color=GLOW)
        self._word_lbl.pack(anchor="w", pady=(6,0))

        badges = ctk.CTkFrame(top, fg_color="transparent"); badges.pack(side="right")

        tb = _card2(badges, border_color=BORDER_A); tb.pack(side="left", padx=(0,8))
        _lbl(tb, "time", size=10, color=ACCENT).pack(padx=14, pady=(8,0))
        self._timer_lbl = _lbl(tb, "30", size=26, weight="bold", color=ACCENT)
        self._timer_lbl.pack(padx=14, pady=(0,8))

        fb = _card2(badges, border_color="#7C2D2D"); fb.pack(side="left")
        _lbl(fb, "forbidden", size=10, color=RED).pack(padx=14, pady=(8,0))
        self._forb_lbl = _lbl(fb, "?", size=26, weight="bold", color=RED)
        self._forb_lbl.pack(padx=14, pady=(0,8))

        self._hint_lbl = _lbl(hdr, "", size=11, color=DIM)
        self._hint_lbl.pack(anchor="w", padx=18, pady=(8,16))

    def _build_input_card(self, parent, submit_fn):
        inp = _card(parent); inp.pack(fill="x", pady=(0,10))
        self._entry = _entry(inp, "Type your word and press Enter…")
        self._entry.pack(fill="x", padx=16, pady=(16,10))
        self._entry.bind("<Return>", lambda e: submit_fn())
        br = ctk.CTkFrame(inp, fg_color="transparent"); br.pack(fill="x", padx=16, pady=(0,10))
        self._play_btn = _btn_solid(br, "▶  Play Word", submit_fn, height=42)
        self._play_btn.pack(side="left", fill="x", expand=True, padx=(0,8))
        _btn(br, "Skip", lambda: self._do_skip(self.current if hasattr(self,"current") else 1),
             color=ORANGE, height=42).pack(side="left", fill="x", expand=True)
        self._msg_lbl = _lbl(inp, "", size=11, color=DIM, wraplength=400)
        self._msg_lbl.pack(padx=16, pady=(0,14))

    def _update_ui(self):
        if not hasattr(self, "_turn_lbl") or not self._turn_lbl.winfo_exists(): return
        w, last = self.prevword, self.prevword[-1]
        is_bot = self.current == self.bot_num
        self._turn_lbl.configure(
            text="🤖  Bot is thinking…" if is_bot else f"Player {self.current}'s turn",
            text_color=GLOW if is_bot else ACCENT)
        self._word_lbl.configure(text=w)
        self._hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._forb_lbl.configure(text=self.forbidden.upper())
        if hasattr(self,"_entry"):
            self._entry.configure(state="disabled" if is_bot else "normal")
            if hasattr(self,"_play_btn"): self._play_btn.configure(state="disabled" if is_bot else "normal")
            if not is_bot: self._entry.focus()
        if hasattr(self,"_chain_box") and self._chain_box.winfo_exists():
            self._chain_box.configure(state="normal")
            self._chain_box.delete("1.0","end")
            self._chain_box.insert("end", "  →  ".join(self.wordlist))
            self._chain_box.configure(state="disabled")
            self._chain_cnt.configure(text=str(len(self.wordlist)))
        for i in range(1, self.n_players + 1):
            out = i not in self.active; active = i == self.current and not out
            is_bot_p = i == self.bot_num
            self._sc_pts[i].configure(text=str(self.scores[i-1]))
            if out:
                self._sc_cards[i].configure(border_color="#3D0000")
                self._sc_pts[i].configure(text_color=RED_B)
                self._sc_names[i].configure(text_color=DIM)
            elif active:
                col_bg = "#1e1238" if is_bot_p else "#0e1e38"
                self._sc_cards[i].configure(border_color=GLOW if is_bot_p else ACCENT,
                                             fg_color=(col_bg, col_bg))
                self._sc_pts[i].configure(text_color=GLOW)
                self._sc_names[i].configure(text_color=TEXT)
            else:
                self._sc_cards[i].configure(fg_color=CARD2, border_color=BORDER)
                self._sc_pts[i].configure(text_color=GLOW if is_bot_p else DIM)
                self._sc_names[i].configure(text_color=GLOW if is_bot_p else DIM)

    def _start_timer(self):
        if self._timer_id: self.after_cancel(self._timer_id)
        self.time_left = 30; self._tick()

    def _tick(self):
        if not self._game_active: return
        t = self.time_left
        if hasattr(self,"_timer_lbl") and self._timer_lbl.winfo_exists():
            self._timer_lbl.configure(text=str(t), text_color=RED_B if t<=10 else ACCENT)
        if t <= 0:
            if not hasattr(self,"bot_num") or self.current != self.bot_num:
                self._do_skip(self.current)
            return
        self.time_left -= 1; self._timer_id = self.after(1000, self._tick)

    def _do_bot_turn(self):
        if not self._game_active or self.current != self.bot_num: return
        word = bot_pick_word(self.prevword[-1], self.wset, self.forbidden, self.bot_diff)
        if word is None: self._do_skip(self.bot_num); return
        danger_pct = 100 - self.bot_diff
        if hasattr(self,"_bot_play_lbl") and self._bot_play_lbl.winfo_exists():
            self._bot_play_lbl.configure(text=f"Danger pool: {danger_pct}%")
        if word[-1] == self.forbidden:
            self._eliminate(self.bot_num,
                f"🤖 Bot played '{word}' — forbidden ending! Bot is out."); return
        self.wordlist.append(word); self.wset.add(word)
        self.scores[self.bot_num-1] += len(word); self.prevword = word
        self._set_msg(f"🤖 Bot played '{word}'  (+{len(word)} pts)", GLOW)
        self.current = self._next(); self._update_ui(); self._start_timer()

    def _bot_submit(self):
        if self.current == self.bot_num: return
        raw = self._entry.get().strip().lower(); self._entry.delete(0,"end")
        if not raw: return
        if raw == "/help":
            self._set_msg("/skip · /donate <pts> <p> · /wordlist · /help", ACCENT); return
        if raw == "/wordlist":
            self._set_msg("Used: " + ", ".join(self.wordlist), ACCENT); return
        if raw == "/skip": self._do_skip(self.current); return
        if raw.startswith("/donate"): self._do_donate(self.current, raw); return
        self._process_word_local(self.current, raw, is_bot_game=True)

    def _process_word_local(self, p, word, is_bot_game=False):
        if word in self.wset:
            self._set_msg("Already used — pick a different word.", RED); return
        if dictionary_set and word not in dictionary_set:
            self._set_msg(f'"{word}" — not a valid English word.', RED); return
        if word[0] != self.prevword[-1]:
            self._set_msg(f'Must start with "{self.prevword[-1]}".', RED); return
        if word[-1] == self.forbidden:
            self._eliminate(p, f"Player {p} is out! Ended with forbidden '{self.forbidden}'."); return
        self.wordlist.append(word); self.wset.add(word)
        self.scores[p-1] += len(word); self.prevword = word
        self._set_msg(f"+{len(word)} pts for Player {p}.", GREEN)
        self.current = self._next(); self._update_ui()
        if is_bot_game and self.current == self.bot_num:
            self.after(900, self._do_bot_turn)
        else:
            self._start_timer()

    def _do_skip(self, p):
        name = "🤖 Bot" if hasattr(self,"bot_num") and p==self.bot_num else f"Player {p}"
        o = random.randint(0,2)
        if o == 0:
            self.scores[p-1] = max(0, self.scores[p-1]-10)
            self._set_msg(f"{name} skipped — lost 10 pts.", ORANGE)
        elif o == 1:
            self._set_msg(f"{name} skipped safely.", GREEN)
        else:
            self._eliminate(p, f"{name} skipped and was eliminated!"); return
        self.current = self._next(); self._update_ui()
        if hasattr(self,"bot_num") and self.current==self.bot_num:
            self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _do_donate(self, p, raw):
        parts = raw.split()
        if len(parts) != 3: self._set_msg("/donate <pts> <player>", RED); return
        try: amt, target = int(parts[1]), int(parts[2])
        except ValueError: self._set_msg("/donate <pts> <player>", RED); return
        if amt<=0 or target<1 or target>self.n_players or target==p or target not in self.active:
            self._set_msg("Invalid target.", RED); return
        actual = min(amt, self.scores[p-1])
        self.scores[p-1] -= actual; self.scores[target-1] += actual
        tn = "🤖 Bot" if hasattr(self,"bot_num") and target==self.bot_num else f"Player {target}"
        self._set_msg(f"Player {p} donated {actual} pts to {tn}.", ACCENT)
        self.current = self._next(); self._update_ui()
        if hasattr(self,"bot_num") and self.current==self.bot_num:
            self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _eliminate(self, p, msg):
        next_p = self._next(); self.active.remove(p)
        is_bot = hasattr(self,"bot_num") and p==self.bot_num
        self._set_msg(msg, GLOW if is_bot else ORANGE)
        self._update_ui()
        if len(self.active) == 1:
            if self._timer_id: self.after_cancel(self._timer_id); self._timer_id = None
            self.after(1400, lambda: self._end_game(self.active[0])); return
        self.current = next_p
        if hasattr(self,"bot_num") and self.current==self.bot_num:
            self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _next(self):
        idx = self.active.index(self.current)
        return self.active[(idx+1) % len(self.active)]

    def _end_game(self, winner):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=64, pady=40)
        is_bot = hasattr(self,"bot_num") and winner==self.bot_num
        _lbl(root, "✦", size=56, color=GLOW if is_bot else ACCENT).pack(pady=(0,4))
        _lbl(root, "Game Over", size=28, weight="bold").pack()
        wtxt = "🤖 Bot wins!" if is_bot else f"Player {winner} wins!"
        _lbl(root, wtxt, size=16, weight="bold", color=GLOW if is_bot else ACCENT).pack(pady=(6,20))
        card = _card(root); card.pack(fill="x", pady=(0,22))
        _lbl(card, "Final Scores", size=12, color=DIM).pack(anchor="w", padx=20, pady=(16,8))
        n = self.n_players if hasattr(self,"n_players") else self.l_nplayers
        sc = self.scores if hasattr(self,"scores") else self.l_scores
        act = self.active if hasattr(self,"active") else self.l_active
        for i in sorted(range(1,n+1), key=lambda x:sc[x-1], reverse=True):
            out=i not in act; is_w=i==winner
            ib=hasattr(self,"bot_num") and i==self.bot_num
            name="🤖 Bot" if ib else f"Player {i}"
            col=GLOW if (is_w and ib) else (ACCENT if is_w else (RED_B if out else DIM))
            row=_card2(card); row.pack(fill="x", padx=16, pady=3)
            _lbl(row, name+(" · out" if out else "")+(" 🏆" if is_w else ""),
                 size=13, weight="bold" if is_w else "normal", color=col).pack(
                side="left", padx=14, pady=10)
            _lbl(row, f"{sc[i-1]} pts", size=13, color=col).pack(side="right", padx=14)
        wlen = len(self.wordlist) if hasattr(self,"wordlist") else len(self.l_wordlist)
        extras = [f"Words played: {wlen}"]
        if hasattr(self,"bot_diff"): extras.append(f"Final bot difficulty: {self.bot_diff}/100")
        _lbl(card, "  ·  ".join(extras), size=11, color=DIM).pack(
            anchor="w", padx=20, pady=(4,16))
        _btn_solid(root, "Play Again", self._show_lobby, height=48).pack(fill="x", pady=(0,10))
        _btn(root, "⛶  Fullscreen", self._toggle_fs, color=DIM, height=38).pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  LOCAL SETUP + GAME
    # ══════════════════════════════════════════════════════════════════════════
    def _show_local_setup(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=56)
        _lbl(root, "Local Play", size=26, weight="bold", color=ACCENT).pack(pady=(0,28))
        card = _card(root); card.pack(fill="x", pady=(0,20))
        _lbl(card, "Number of players", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(18,8))
        self._lpvar = ctk.IntVar(value=2)
        pr = ctk.CTkFrame(card, fg_color="transparent"); pr.pack(fill="x", padx=20, pady=(0,6))
        self._lslbl = _lbl(pr, "2 players", size=13, weight="bold", color=GLOW, width=90)
        _slider(card, self._lpvar, 2, 8, steps=6,
                command=lambda v: self._lslbl.configure(text=f"{int(v)} players")).pack(
            fill="x", padx=20, pady=(0,6))
        self._lslbl.pack(in_=pr, side="right")
        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()
        _btn_solid(root, "Start Game", self._start_local_game, height=48).pack(fill="x", pady=(0,10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=38).pack(fill="x")

    def _start_local_game(self):
        n = int(self._lpvar.get())
        self.bot_num = None
        self.n_players = n; self.scores = [0]*n; self.active = list(range(1,n+1))
        self.wordlist = ["apple"]; self.wset = {"apple"}
        self.forbidden = chr(random.randint(ord("a"), ord("z")))
        self.current = 1; self.prevword = "apple"; self.notepad = []
        self._show_local_game()

    def _show_local_game(self):
        self._clear(); self._game_active = True
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=14, pady=14)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        self._build_game_header(left)
        self._build_input_card(left, submit_fn=self._local_submit)

        chain = _card(left); chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent"); cr.pack(fill="x", padx=14, pady=(12,4))
        _lbl(cr, "Word chain", size=12, color=DIM).pack(side="left")
        self._chain_cnt = _lbl(cr, "1", size=13, weight="bold", color=ACCENT)
        self._chain_cnt.pack(side="right")
        self._chain_box = ctk.CTkTextbox(chain, font=_F(12), fg_color=CARD2,
                                          activate_scrollbars=True, wrap="word",
                                          text_color=TEXT, corner_radius=10)
        self._chain_box.pack(fill="both", expand=True, padx=14, pady=(0,12))
        self._chain_box.configure(state="disabled")

        sc_cards, sc_pts, sc_names, _, np_box, np_entry, np_msg = _build_right_panel(
            self, outer, self.n_players, show_commands=True, toggle_fs=self._toggle_fs)
        self._sc_cards = sc_cards; self._sc_pts = sc_pts; self._sc_names = sc_names
        self._np_box = np_box; self._np_entry = np_entry; self._np_msg = np_msg
        np_entry.bind("<Return>", lambda e: _notepad_enter_fn(
            self, np_entry.get, np_entry, np_msg, np_box, self.notepad))

        self._entry.focus(); self._update_ui(); self._start_timer()

    def _local_submit(self):
        raw = self._entry.get().strip().lower(); self._entry.delete(0,"end")
        if not raw: return
        p = self.current
        if raw == "/help":
            self._set_msg("/skip · /donate <pts> <p> · /wordlist · /help", ACCENT); return
        if raw == "/wordlist":
            self._set_msg("Used: " + ", ".join(self.wordlist), ACCENT); return
        if raw == "/skip": self._do_skip(p); return
        if raw.startswith("/donate"): self._do_donate(p, raw); return
        self._process_word_local(p, raw, is_bot_game=False)

    # ══════════════════════════════════════════════════════════════════════════
    #  NETWORK — HOST SETUP
    # ══════════════════════════════════════════════════════════════════════════
    def _show_host_setup(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=56)
        _lbl(root, "Host a Game", size=26, weight="bold", color=ACCENT).pack(pady=(0,28))
        card = _card(root); card.pack(fill="x", pady=(0,20))
        _lbl(card, "Number of players", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(18,8))
        self._hpvar = ctk.IntVar(value=2)
        pr = ctk.CTkFrame(card, fg_color="transparent"); pr.pack(fill="x", padx=20, pady=(0,6))
        self._hslbl = _lbl(pr, "2 players", size=13, weight="bold", color=GLOW, width=90)
        _slider(card, self._hpvar, 2, 8, steps=6,
                command=lambda v: self._hslbl.configure(text=f"{int(v)} players")).pack(
            fill="x", padx=20, pady=(0,6))
        self._hslbl.pack(in_=pr, side="right")
        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()
        self._herr = _lbl(root, "", size=11, color=RED_B); self._herr.pack()
        _btn_solid(root, "Create Lobby", self._create_lobby, height=48).pack(
            fill="x", pady=(8,10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=38).pack(fill="x")

    def _create_lobby(self):
        n = int(self._hpvar.get())
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
        if msg["type"]=="player_joined" and hasattr(self,"_conn_lbl") and self._conn_lbl.winfo_exists():
            self._conn_lbl.configure(text=f"{msg['count']}/{self.server.num_players} connected")

    # ══════════════════════════════════════════════════════════════════════════
    #  NETWORK — JOIN
    # ══════════════════════════════════════════════════════════════════════════
    def _show_join(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=56)
        _lbl(root, "Join a Game", size=26, weight="bold", color=ACCENT).pack(pady=(0,28))
        card = _card(root); card.pack(fill="x", pady=(0,20))
        _lbl(card, "Host IP address", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(18,8))
        self._ip_entry = _entry(card, "192.168.X.XX", height=46)
        self._ip_entry.pack(fill="x", padx=20, pady=(0,12))
        self._ip_entry.bind("<Return>", lambda e: self._do_join())
        history = load_ip_history()
        if history:
            _lbl(card, "Recent", size=11, color=DIM).pack(anchor="w", padx=20, pady=(0,4))
            self._ip_dropdown = ctk.CTkOptionMenu(
                card, values=history, font=_F(13), height=38, corner_radius=14,
                fg_color=CARD2, button_color=BORDER_A, button_hover_color="#5B21B6",
                dropdown_fg_color=CARD, dropdown_hover_color="#1E1035",
                text_color=TEXT, dropdown_text_color=TEXT,
                command=lambda v: (self._ip_entry.delete(0,"end"), self._ip_entry.insert(0,v)))
            self._ip_dropdown.pack(fill="x", padx=20, pady=(0,6))
            self._ip_dropdown.set("Select recent IP…")
            _btn(card, "Clear history",
                 lambda: (save_config({k:v for k,v in load_config().items() if k!="ip_history"}),
                          self._show_join()),
                 color=DIM, size=11, height=28).pack(anchor="e", padx=20, pady=(0,14))
        else:
            ctk.CTkFrame(card, height=4, fg_color="transparent").pack()
        self._msg_lbl = _lbl(root, "", size=11, color=DIM); self._msg_lbl.pack(pady=(0,8))
        _btn_solid(root, "Connect", self._do_join, height=48).pack(fill="x", pady=(0,10))
        _btn(root, "← Back", self._show_lobby, color=DIM, height=38).pack(fill="x")
        self._ip_entry.focus()

    def _do_join(self):
        ip = self._ip_entry.get().strip()
        if not ip: self._set_msg("Enter an IP address.", RED); return
        self._set_msg("Connecting…", ACCENT)
        save_ip_to_history(ip)
        self.client = GameClient(lambda msg: self.after(0, self._on_client_msg, msg),
                                 on_disconnect=lambda: self.after(0, self._on_disconnect))
        threading.Thread(target=lambda: self._try_connect(ip), daemon=True).start()

    def _try_connect(self, ip):
        try: self.client.connect(ip)
        except Exception as e: self.after(0, lambda: self._set_msg(f"Failed: {e}", RED))

    # ══════════════════════════════════════════════════════════════════════════
    #  NETWORK — WAITING ROOM + GAME
    # ══════════════════════════════════════════════════════════════════════════
    def _show_waiting_room(self, is_host=False, total=None):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=56)
        _lbl(root, "Lobby", size=26, weight="bold", color=ACCENT).pack(pady=(0,8))
        _lbl(root, "Waiting for players…", size=13, color=DIM).pack(pady=(0,28))
        if is_host:
            ip = get_local_ip()
            card = _card(root); card.pack(fill="x", pady=(0,22))
            _lbl(card, "Your IP — share with players", size=11, color=DIM).pack(
                anchor="w", padx=20, pady=(18,8))
            ibox = ctk.CTkFrame(card, fg_color=CARD2, corner_radius=12)
            ibox.pack(fill="x", padx=20, pady=(0,8))
            _lbl(ibox, ip, size=26, weight="bold", color=GLOW).pack(padx=20, pady=16)
            _lbl(card, f"Port: {PORT}", size=11, color=DIM).pack(
                anchor="w", padx=20, pady=(0,16))
        t = f"0/{total} connected" if is_host else "Connecting…"
        self._conn_lbl = _lbl(root, t, size=14, color=ACCENT); self._conn_lbl.pack(pady=8)
        self._msg_lbl = _lbl(root, "Game starts when all players join.", size=11, color=DIM)
        self._msg_lbl.pack()

    def _on_client_msg(self, msg):
        t = msg.get("type")
        if t == "welcome":
            self.player_num = msg["player_num"]; self.g_nplayers = msg["num_players"]
            if not (hasattr(self,"_conn_lbl") and self._conn_lbl.winfo_exists()):
                self._show_waiting_room()
            if hasattr(self,"_conn_lbl") and self._conn_lbl.winfo_exists():
                self._conn_lbl.configure(text=f"You are Player {self.player_num} — waiting…")
        elif t == "tick":
            tv = msg.get("time_left",30)
            if hasattr(self,"_g_timer_lbl") and self._g_timer_lbl.winfo_exists():
                self._g_timer_lbl.configure(text=str(tv),
                                             text_color=RED_B if tv<=10 else ACCENT)
        elif t == "game_start":
            self._apply_net_state(msg); self._show_net_game()
        elif t == "state_update":
            self._apply_net_state(msg)
            if self._game_active: self._update_net_ui()
            if msg.get("msg"): self._set_msg(msg["msg"], msg.get("color", ACCENT))
        elif t == "msg":
            self._set_msg(msg["text"], msg.get("color", ACCENT))
        elif t == "game_end":
            self._apply_net_state(msg); self._show_net_end(msg["winner"], msg.get("msg",""))

    def _apply_net_state(self, msg):
        self.g_current = msg.get("current_player",1)
        self.g_prev_word = msg.get("previous_word","apple")
        self.g_wordlist = msg.get("wordlist",[])
        self.g_scores = msg.get("scores",[])
        self.g_active = msg.get("active_players",[])
        self.g_forbidden = msg.get("forbidden","?")
        self.g_nplayers = msg.get("num_players", getattr(self,"g_nplayers",2))

    def _show_net_game(self):
        self._clear(); self._game_active = True; self.g_notepad = []
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=14, pady=14)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        hdr = _card(left); hdr.pack(fill="x", pady=(0,10))
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(18,0))

        wc = ctk.CTkFrame(top, fg_color="transparent")
        wc.pack(side="left", fill="x", expand=True)
        self._turn_lbl = _lbl(wc, "", size=12, color=DIM); self._turn_lbl.pack(anchor="w")
        _lbl(wc, f"✦  You are Player {self.player_num}", size=11, color=ACCENT).pack(anchor="w")
        self._word_lbl = _lbl(wc, "", size=34, weight="bold", color=GLOW)
        self._word_lbl.pack(anchor="w", pady=(6,0))

        badges = ctk.CTkFrame(top, fg_color="transparent"); badges.pack(side="right")
        tb = _card2(badges, border_color=BORDER_A); tb.pack(side="left", padx=(0,8))
        _lbl(tb, "time", size=10, color=ACCENT).pack(padx=14, pady=(8,0))
        self._g_timer_lbl = _lbl(tb, "30", size=26, weight="bold", color=ACCENT)
        self._g_timer_lbl.pack(padx=14, pady=(0,8))

        fb = _card2(badges, border_color="#7C2D2D"); fb.pack(side="left")
        _lbl(fb, "forbidden", size=10, color=RED).pack(padx=14, pady=(8,0))
        self._g_forb_lbl = _lbl(fb, "?", size=26, weight="bold", color=RED)
        self._g_forb_lbl.pack(padx=14, pady=(0,8))

        self._g_hint_lbl = _lbl(hdr, "", size=11, color=DIM)
        self._g_hint_lbl.pack(anchor="w", padx=18, pady=(8,16))

        inp = _card(left); inp.pack(fill="x", pady=(0,10))
        self._entry = _entry(inp, "Type your word and press Enter…")
        self._entry.pack(fill="x", padx=16, pady=(16,10))
        self._entry.bind("<Return>", lambda e: self._net_submit())
        br = ctk.CTkFrame(inp, fg_color="transparent"); br.pack(fill="x", padx=16, pady=(0,10))
        self._play_btn = _btn_solid(br, "▶  Play Word", self._net_submit, height=42)
        self._play_btn.pack(side="left", fill="x", expand=True, padx=(0,8))
        _btn(br, "Skip", lambda: self.client.send_action("/skip"),
             color=ORANGE, height=42).pack(side="left", fill="x", expand=True)
        self._msg_lbl = _lbl(inp, "", size=11, color=DIM, wraplength=400)
        self._msg_lbl.pack(padx=16, pady=(0,14))

        chain = _card(left); chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent"); cr.pack(fill="x", padx=14, pady=(12,4))
        _lbl(cr, "Word chain", size=12, color=DIM).pack(side="left")
        self._g_chain_cnt = _lbl(cr, "0", size=13, weight="bold", color=ACCENT)
        self._g_chain_cnt.pack(side="right")
        self._g_chain_box = ctk.CTkTextbox(chain, font=_F(12), fg_color=CARD2,
                                            activate_scrollbars=True, wrap="word",
                                            text_color=TEXT, corner_radius=10)
        self._g_chain_box.pack(fill="both", expand=True, padx=14, pady=(0,12))
        self._g_chain_box.configure(state="disabled")

        self._g_sc_cards = {}; self._g_sc_pts = {}; self._g_sc_names = {}
        right = _card(outer); right.configure(width=226)
        right.pack(side="right", fill="y"); right.pack_propagate(False)

        sh = ctk.CTkFrame(right, fg_color="transparent"); sh.pack(fill="x", padx=14, pady=(16,6))
        _lbl(sh, "Scores", size=14, weight="bold", color=GLOW).pack(side="left")
        for i in range(1, self.g_nplayers+1):
            f = _card2(right, border_color=BORDER); f.pack(fill="x", padx=10, pady=2)
            you = " (you)" if i==self.player_num else ""
            n = _lbl(f, f"Player {i}{you}", size=12, color=ACCENT if you else DIM)
            n.pack(side="left", padx=(12,4), pady=8)
            p = _lbl(f, "0", size=13, weight="bold", color=ACCENT)
            p.pack(side="right", padx=12)
            self._g_sc_cards[i]=f; self._g_sc_pts[i]=p; self._g_sc_names[i]=n

        _divider(right)
        _lbl(right, "Notepad", size=12, weight="bold").pack(padx=12, pady=(0,4))
        self._g_np_box = ctk.CTkTextbox(right, font=_F(11), fg_color=CARD2,
                                         activate_scrollbars=True, wrap="word",
                                         height=80, text_color=TEXT, corner_radius=10)
        self._g_np_box.pack(fill="x", padx=10, pady=(0,4))
        self._g_np_box.configure(state="disabled")
        self._g_np_entry = _entry(right, "word → Enter to save", height=32)
        self._g_np_entry.pack(fill="x", padx=10, pady=(0,2))
        self._g_np_msg = _lbl(right, "", size=10, color=DIM)
        self._g_np_msg.pack(padx=10, pady=(0,4))
        self._g_np_entry.bind("<Return>", lambda e: _notepad_enter_fn(
            self, self._g_np_entry.get, self._g_np_entry,
            self._g_np_msg, self._g_np_box, self.g_notepad))

        _divider(right)
        _lbl(right, "commands", size=10, color=DIM).pack()
        for cmd in ["/skip", "/donate <pts> <p>", "/wordlist", "/help"]:
            _lbl(right, cmd, size=10, color=ACCENT).pack(pady=1)
        _divider(right)
        _btn(right, "⛶  Fullscreen", self._toggle_fs, color=DIM, size=10,
             height=28).pack(fill="x", padx=10, pady=(0,10))

        self._update_net_ui()

    def _update_net_ui(self):
        if not self.g_wordlist: return
        my_turn = self.g_current == self.player_num
        w, last = self.g_prev_word, self.g_prev_word[-1]
        self._turn_lbl.configure(
            text="✦  Your turn!" if my_turn else f"Player {self.g_current}'s turn",
            text_color=ACCENT if my_turn else DIM)
        self._word_lbl.configure(text=w)
        self._g_hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._g_forb_lbl.configure(text=self.g_forbidden.upper())
        self._entry.configure(state="normal" if my_turn else "disabled")
        self._play_btn.configure(state="normal" if my_turn else "disabled")
        if my_turn: self._entry.focus()
        self._g_chain_box.configure(state="normal")
        self._g_chain_box.delete("1.0","end")
        self._g_chain_box.insert("end","  →  ".join(self.g_wordlist))
        self._g_chain_box.configure(state="disabled")
        self._g_chain_cnt.configure(text=str(len(self.g_wordlist)))
        for i in range(1, self.g_nplayers+1):
            out=i not in self.g_active; active=i==self.g_current and not out
            score=self.g_scores[i-1] if i<=len(self.g_scores) else 0
            self._g_sc_pts[i].configure(text=str(score))
            if out:
                self._g_sc_cards[i].configure(border_color="#3D0000")
                self._g_sc_pts[i].configure(text_color=RED_B)
                self._g_sc_names[i].configure(text_color=DIM)
            elif active:
                self._g_sc_cards[i].configure(border_color=ACCENT)
                self._g_sc_pts[i].configure(text_color=GLOW)
                self._g_sc_names[i].configure(text_color=TEXT)
            else:
                self._g_sc_cards[i].configure(border_color=BORDER)
                self._g_sc_pts[i].configure(text_color=DIM)
                self._g_sc_names[i].configure(text_color=DIM)

    def _net_submit(self):
        if self.g_current != self.player_num: return
        raw = self._entry.get().strip().lower(); self._entry.delete(0,"end")
        if not raw: return
        if raw in ("/help","/wordlist","/rules"):
            self._set_msg("Use /skip · /donate <pts> <p> · /wordlist", ACCENT); return
        self.client.send_action(raw)

    def _show_net_end(self, winner, extra=""):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=64, pady=40)
        is_me = winner == self.player_num
        _lbl(root, "✦", size=52, color=ACCENT if is_me else DIM).pack(pady=(0,4))
        _lbl(root, "Game Over", size=28, weight="bold").pack()
        msg = f"Player {winner} wins!" + (" — that's you! 🏆" if is_me else "")
        _lbl(root, msg, size=16, weight="bold", color=GLOW if is_me else RED_B).pack(pady=(6,4))
        if extra: _lbl(root, extra[:70], size=11, color=DIM).pack(pady=(0,16))
        card = _card(root); card.pack(fill="x", pady=(8,22))
        _lbl(card, "Final Scores", size=12, color=DIM).pack(anchor="w", padx=20, pady=(16,8))
        for i in sorted(range(1,self.g_nplayers+1),
                        key=lambda x:self.g_scores[x-1] if x<=len(self.g_scores) else 0, reverse=True):
            out=i not in self.g_active; is_w=i==winner
            you=" (you)" if i==self.player_num else ""
            col=GLOW if is_w else (RED_B if out else DIM)
            score=self.g_scores[i-1] if i<=len(self.g_scores) else 0
            row=_card2(card); row.pack(fill="x", padx=16, pady=3)
            _lbl(row, f"Player {i}{you}"+(" · out" if out else "")+(" 🏆" if is_w else ""),
                 size=13, weight="bold" if is_w else "normal", color=col).pack(
                side="left", padx=14, pady=10)
            _lbl(row, f"{score} pts", size=13, color=col).pack(side="right", padx=14)
        _lbl(card, f"Words played: {len(self.g_wordlist)}", size=11, color=DIM).pack(
            anchor="w", padx=20, pady=(4,16))
        _btn_solid(root, "← Back to Lobby", self._show_lobby, height=48).pack(fill="x")

    def _on_disconnect(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=88, pady=88)
        _lbl(root, "✦", size=44, color=RED).pack(pady=(0,8))
        _lbl(root, "Disconnected", size=22, weight="bold", color=RED_B).pack(pady=(0,8))
        _lbl(root, "Connection to host was lost.", size=13, color=DIM).pack(pady=(0,32))
        _btn_solid(root, "← Back to Lobby", self._show_lobby, height=48).pack(fill="x")


if __name__ == "__main__":
    app = ShiritoriApp()
    app.mainloop()
