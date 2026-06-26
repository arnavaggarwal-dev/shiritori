# ─────────────────────────────────────────────────────────────────────────────
#  Shiritori — Bot Edition  ✦ cosmic nebula theme
#  pip install customtkinter
#
#  pyinstaller --onefile --windowed
#    --add-data "words_dictionary.json;."
#    --add-data "C:\path\to\customtkinter;customtkinter"
#    shiritori_bot.py
# ─────────────────────────────────────────────────────────────────────────────

import customtkinter as ctk
import random, json, sys, os
from collections import defaultdict

def resource_path(f):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, f)

try:
    with open(resource_path("words_dictionary.json")) as f:
        dictionary = list(json.load(f).keys())
    dictionary_set = set(dictionary)
except FileNotFoundError:
    dictionary = []; dictionary_set = set()

# ── word complexity scoring ───────────────────────────────────────────────────
WORDS_BY_LETTER = defaultdict(list)
for w in dictionary:
    WORDS_BY_LETTER[w[0]].append(w)

def bot_pick_word(start, wset, forbidden, difficulty):
    """
    Build a pool where difficulty% are safe words and (100-difficulty)% are
    forbidden-ending words. Bot picks randomly — if it lands a forbidden-ending
    word it gets eliminated by the caller. difficulty=100 → never picks suicidal
    word (hardest); difficulty=0 → only picks suicidal words (easiest).
    """
    cands = [w for w in WORDS_BY_LETTER.get(start, [])
             if w not in wset and len(w) > 1]
    if not cands: return None
    safe   = [w for w in cands if w[-1] != forbidden]
    danger = [w for w in cands if w[-1] == forbidden]
    danger_n = round(len(danger) * (100 - difficulty) / 100)
    safe_n   = round(len(safe)   * difficulty / 100)
    pool = (random.sample(danger, min(danger_n, len(danger))) +
            random.sample(safe,   min(safe_n,   len(safe))))
    if not pool:
        pool = safe if safe else danger
    if danger and random.random() < 0.01:
        return random.choice(danger)
    return random.choice(pool)

# ── cosmic nebula palette (matches shiritori_net) ─────────────────────────────
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

def _F(size, weight="normal"):
    return ctk.CTkFont(size=size, weight=weight)

def _card(parent, border_color=None, **kw):
    return ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _card2(parent, border_color=None, **kw):
    return ctk.CTkFrame(parent, corner_radius=10, fg_color=CARD2,
                        border_width=1, border_color=border_color or BORDER, **kw)

def _btn(parent, text, command, color=None, size=13, **kw):
    c = color or ACCENT
    return ctk.CTkButton(parent, text=text, font=_F(size, "bold"), command=command,
                         corner_radius=10, fg_color=CARD2, hover_color="#1E1035",
                         border_width=1, border_color=c, text_color=c, **kw)

def _btn_solid(parent, text, command, size=13, **kw):
    return ctk.CTkButton(parent, text=text, font=_F(size, "bold"), command=command,
                         corner_radius=10, fg_color="#4C1D95", hover_color="#5B21B6",
                         text_color=TEXT, **kw)

def _entry(parent, placeholder="", **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, font=_F(13),
                        corner_radius=10, fg_color=CARD2, border_color=BORDER,
                        border_width=1, text_color=TEXT, placeholder_text_color=DIM, **kw)

def _lbl(parent, text, size=13, color=None, weight="normal", **kw):
    return ctk.CTkLabel(parent, text=text, font=_F(size, weight),
                        text_color=color or TEXT, **kw)

def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=BORDER, corner_radius=0).pack(
        fill="x", padx=14, pady=6)


class ShiritoriBot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shiritori — Bot Mode")
        self.geometry("780x660")
        self.resizable(True, True)
        self.minsize(660, 560)
        self.configure(fg_color=BG)
        self._fs = False
        self._timer_id = None
        self._game_active = False
        self.bind("<F11>",    lambda e: self._toggle_fs())
        self.bind("<Escape>", lambda e: self._exit_fs())
        self._show_lobby()

    def _toggle_fs(self):
        self._fs = not self._fs; self.attributes("-fullscreen", self._fs)

    def _exit_fs(self):
        if self._fs: self._fs = False; self.attributes("-fullscreen", False)

    def _clear(self):
        self._game_active = False
        if self._timer_id: self.after_cancel(self._timer_id); self._timer_id = None
        for w in self.winfo_children(): w.destroy()

    def _set_msg(self, text, color):
        if hasattr(self, "_msg_lbl") and self._msg_lbl.winfo_exists():
            self._msg_lbl.configure(text=text, text_color=color)

    # ── lobby ─────────────────────────────────────────────────────────────────
    def _show_lobby(self):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=64, pady=44)

        _lbl(root, "✦  SHIRITORI  ✦", size=34, weight="bold", color=ACCENT).pack()
        _lbl(root, "Bot Mode", size=13, color=GLOW).pack(pady=(2, 28))

        # players card
        pc = _card(root)
        pc.pack(fill="x", pady=(0, 10))
        _lbl(pc, "Human players", size=12, color=DIM).pack(anchor="w", padx=20, pady=(16, 6))
        self._pvar  = ctk.IntVar(value=1)
        pr = ctk.CTkFrame(pc, fg_color="transparent")
        pr.pack(fill="x", padx=20, pady=(0, 4))
        self._pslbl = _lbl(pr, "1 player", size=13, weight="bold", color=GLOW, width=90)
        ctk.CTkSlider(pr, from_=1, to=7, number_of_steps=6, variable=self._pvar,
                      progress_color=ACCENT, button_color=GLOW,
                      command=lambda v: self._pslbl.configure(
                          text=f"{int(v)} player{'s' if int(v)>1 else ''}"),
                      ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._pslbl.pack(side="left")
        _lbl(pc, "The bot is always included as an extra player.",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(4, 16))

        # bot difficulty card
        dc = _card(root, border_color=BORDER_A)
        dc.pack(fill="x", pady=(0, 10))
        dh = ctk.CTkFrame(dc, fg_color="transparent")
        dh.pack(fill="x", padx=20, pady=(16, 6))
        _lbl(dh, "Bot starting difficulty", size=12, weight="bold").pack(side="left")
        self._diff_lbl_lobby = _lbl(dh, "50", size=13, weight="bold", color=GLOW)
        self._diff_lbl_lobby.pack(side="right")
        self._diff_var = ctk.IntVar(value=50)
        ctk.CTkSlider(dc, from_=1, to=100, variable=self._diff_var,
                      progress_color=ACCENT, button_color=GLOW,
                      command=lambda v: self._diff_lbl_lobby.configure(text=str(int(v))),
                      ).pack(fill="x", padx=20, pady=(0, 8))

        # difficulty legend
        leg = ctk.CTkFrame(dc, fg_color=CARD2, corner_radius=8)
        leg.pack(fill="x", padx=20, pady=(0, 16))
        lr = ctk.CTkFrame(leg, fg_color="transparent")
        lr.pack(fill="x", padx=12, pady=8)
        for label, col in [("1  Easy", GREEN), ("50  Medium", ORANGE), ("100  Expert", RED_B)]:
            _lbl(lr, label, size=11, color=col).pack(side="left", expand=True)

        _btn_solid(root, "Start Game", self._start_game, height=46).pack(fill="x", pady=(8, 6))
        _lbl(root, "F11 — fullscreen", size=11, color=DIM).pack()

    def _start_game(self):
        n = int(self._pvar.get())
        self.n_humans  = n; self.n_players = n + 1; self.bot_num = n + 1
        self.scores    = [0] * self.n_players
        self.active    = list(range(1, self.n_players + 1))
        self.wordlist  = ["apple"]; self.wset = {"apple"}
        self.forbidden = chr(random.randint(ord("a"), ord("z")))
        self.current   = 1; self.prevword = "apple"
        self.bot_diff  = int(self._diff_var.get()); self.notepad = []
        self._show_game()

    # ── game screen ───────────────────────────────────────────────────────────
    def _show_game(self):
        self._clear(); self._game_active = True
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # header
        hdr = _card(left); hdr.pack(fill="x", pady=(0, 8))
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 0))

        wc = ctk.CTkFrame(top, fg_color="transparent")
        wc.pack(side="left", fill="x", expand=True)
        self._turn_lbl = _lbl(wc, "", size=11, color=DIM); self._turn_lbl.pack(anchor="w")
        self._word_lbl = _lbl(wc, "", size=30, weight="bold", color=GLOW)
        self._word_lbl.pack(anchor="w", pady=(4, 0))

        badges = ctk.CTkFrame(top, fg_color="transparent"); badges.pack(side="right")

        tb = _card2(badges, border_color=BORDER_A); tb.pack(side="left", padx=(0, 8))
        _lbl(tb, "time", size=10, color=ACCENT).pack(padx=12, pady=(6, 0))
        self._timer_lbl = _lbl(tb, "30", size=22, weight="bold", color=ACCENT)
        self._timer_lbl.pack(padx=12, pady=(0, 6))

        fb = _card2(badges, border_color="#7C2D2D"); fb.pack(side="left")
        _lbl(fb, "forbidden", size=10, color=RED).pack(padx=12, pady=(6, 0))
        self._forb_lbl = _lbl(fb, self.forbidden.upper(), size=22, weight="bold", color=RED)
        self._forb_lbl.pack(padx=12, pady=(0, 6))

        self._hint_lbl = _lbl(hdr, "", size=11, color=DIM)
        self._hint_lbl.pack(anchor="w", padx=18, pady=(6, 14))

        # input
        inp = _card(left); inp.pack(fill="x", pady=(0, 8))
        self._entry = _entry(inp, "Type your word and press Enter…")
        self._entry.pack(fill="x", padx=14, pady=(14, 8))
        self._entry.bind("<Return>", lambda e: self._submit())
        self._play_btn = _btn_solid(inp, "Play Word", self._submit, height=40)
        self._play_btn.pack(fill="x", padx=14, pady=(0, 8))
        self._msg_lbl = _lbl(inp, "", size=11, color=DIM, wraplength=380)
        self._msg_lbl.pack(padx=14, pady=(0, 12))

        # chain
        chain = _card(left); chain.pack(fill="both", expand=True)
        cr = ctk.CTkFrame(chain, fg_color="transparent")
        cr.pack(fill="x", padx=14, pady=(10, 4))
        _lbl(cr, "Word chain", size=11, color=DIM).pack(side="left")
        self._chain_cnt = _lbl(cr, "1", size=12, weight="bold", color=ACCENT)
        self._chain_cnt.pack(side="right")
        self._chain_box = ctk.CTkTextbox(chain, font=_F(12), fg_color=CARD2,
                                         activate_scrollbars=True, wrap="word",
                                         text_color=TEXT, corner_radius=8)
        self._chain_box.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._chain_box.configure(state="disabled")

        # ── right panel ───────────────────────────────────────────────────────
        right = _card(outer); right.configure(width=220)
        right.pack(side="right", fill="y"); right.pack_propagate(False)

        # scores
        _lbl(right, "Scores", size=13, weight="bold", color=GLOW).pack(padx=14, pady=(16, 8))
        self._sc_cards = {}; self._sc_pts = {}; self._sc_names = {}
        for i in range(1, self.n_players + 1):
            is_bot = i == self.bot_num
            f = _card2(right, border_color=BORDER); f.pack(fill="x", padx=8, pady=2)
            name  = "🤖 Bot" if is_bot else f"Player {i}"
            nc    = GLOW if is_bot else DIM
            n = _lbl(f, name, size=11, color=nc); n.pack(side="left", padx=(10, 4), pady=7)
            p = _lbl(f, "0", size=12, weight="bold", color=ACCENT if not is_bot else GLOW)
            p.pack(side="right", padx=10)
            self._sc_cards[i] = f; self._sc_pts[i] = p; self._sc_names[i] = n

        # bot difficulty slider (live mid-game)
        _divider(right)
        dh = ctk.CTkFrame(right, fg_color="transparent"); dh.pack(fill="x", padx=12)
        _lbl(dh, "🤖 Difficulty", size=11, weight="bold", color=GLOW).pack(side="left")
        self._diff_badge = _lbl(dh, str(self.bot_diff), size=11, weight="bold", color=GLOW)
        self._diff_badge.pack(side="right")
        self._diff_slider_var = ctk.IntVar(value=self.bot_diff)
        ctk.CTkSlider(right, from_=1, to=100, variable=self._diff_slider_var,
                      progress_color=ACCENT, button_color=GLOW, height=16,
                      command=self._on_diff_change,
                      ).pack(fill="x", padx=12, pady=(4, 2))
        self._diff_desc = _lbl(right, self._diff_label(self.bot_diff), size=10, color=DIM)
        self._diff_desc.pack(padx=12, pady=(0, 2))
        self._bot_word_lbl = _lbl(right, "", size=10, color=GLOW)
        self._bot_word_lbl.pack(padx=12, pady=(0, 4))

        # notepad
        _divider(right)
        nph = ctk.CTkFrame(right, fg_color="transparent"); nph.pack(fill="x", padx=12)
        _lbl(nph, "Notepad", size=11, weight="bold").pack(side="left")
        _lbl(nph, "jot words", size=10, color=DIM).pack(side="right")
        self._notepad_box = ctk.CTkTextbox(right, font=_F(11), fg_color=CARD2,
                                           activate_scrollbars=True, wrap="word",
                                           height=72, text_color=TEXT, corner_radius=8)
        self._notepad_box.pack(fill="x", padx=8, pady=(4, 4))
        self._notepad_box.configure(state="disabled")
        self._notepad_entry = _entry(right, "word → Enter to save", height=30)
        self._notepad_entry.pack(fill="x", padx=8, pady=(0, 2))
        self._notepad_entry.bind("<Return>", lambda e: self._notepad_enter())
        self._notepad_msg = _lbl(right, "", size=10, color=DIM)
        self._notepad_msg.pack(padx=8, pady=(0, 4))

        # commands + fullscreen
        _divider(right)
        _lbl(right, "commands", size=10, color=DIM).pack()
        for cmd in ["/skip", "/donate <pts> <p>", "/wordlist", "/help"]:
            _lbl(right, cmd, size=10, color=ACCENT).pack(pady=1)
        _divider(right)
        _btn(right, "⛶  Fullscreen", self._toggle_fs, color=DIM, size=10,
             height=26).pack(fill="x", padx=8, pady=(0, 10))

        self._entry.focus()
        self._update_ui(); self._start_timer()
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)

    def _diff_label(self, d):
        if d <= 20:  return "easy — short common words"
        if d <= 40:  return "medium-easy"
        if d <= 60:  return "medium"
        if d <= 80:  return "hard — long/rare words"
        return             "expert — maximum complexity"

    def _on_diff_change(self, val):
        self.bot_diff = int(val)
        self._diff_badge.configure(text=str(self.bot_diff))
        self._diff_desc.configure(text=self._diff_label(self.bot_diff))

    def _update_ui(self):
        w, last  = self.prevword, self.prevword[-1]
        is_bot   = self.current == self.bot_num
        self._turn_lbl.configure(
            text="🤖 Bot is thinking…" if is_bot else f"Player {self.current}'s turn")
        self._word_lbl.configure(text=w)
        self._hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._forb_lbl.configure(text=self.forbidden.upper())
        self._entry.configure(state="disabled" if is_bot else "normal")
        self._play_btn.configure(state="disabled" if is_bot else "normal")
        if not is_bot: self._entry.focus()
        self._chain_box.configure(state="normal")
        self._chain_box.delete("1.0", "end")
        self._chain_box.insert("end", "  →  ".join(self.wordlist))
        self._chain_box.configure(state="disabled")
        self._chain_cnt.configure(text=str(len(self.wordlist)))
        for i in range(1, self.n_players + 1):
            out    = i not in self.active
            active = i == self.current and not out
            is_bot_p = i == self.bot_num
            self._sc_pts[i].configure(text=str(self.scores[i - 1]))
            if out:
                self._sc_cards[i].configure(border_color="#3D0000")
                self._sc_pts[i].configure(text_color=RED_B)
                self._sc_names[i].configure(text_color=DIM)
            elif active:
                col = "#2a1a44" if is_bot_p else "#1a2a44"
                self._sc_cards[i].configure(border_color=ACCENT)
                self._sc_cards[i].configure(fg_color=(col, col))
                self._sc_pts[i].configure(text_color=GLOW)
                self._sc_names[i].configure(text_color=TEXT)
            else:
                self._sc_cards[i].configure(fg_color=CARD2, border_color=BORDER)
                self._sc_pts[i].configure(text_color=GLOW if is_bot_p else DIM)
                self._sc_names[i].configure(text_color=GLOW if is_bot_p else DIM)

    # ── timer ─────────────────────────────────────────────────────────────────
    def _start_timer(self):
        if self._timer_id: self.after_cancel(self._timer_id)
        self.time_left = 30; self._tick()

    def _tick(self):
        if not self._game_active: return
        t = self.time_left
        if hasattr(self, "_timer_lbl") and self._timer_lbl.winfo_exists():
            self._timer_lbl.configure(text=str(t), text_color=RED_B if t <= 10 else ACCENT)
        if t <= 0:
            if self.current != self.bot_num: self._do_skip(self.current)
            return
        self.time_left -= 1; self._timer_id = self.after(1000, self._tick)

    # ── bot turn ──────────────────────────────────────────────────────────────
    def _do_bot_turn(self):
        if not self._game_active or self.current != self.bot_num: return
        word = bot_pick_word(self.prevword[-1], self.wset, self.forbidden, self.bot_diff)
        if word is None: self._do_skip(self.bot_num); return
        danger_pct = 100 - self.bot_diff
        self._bot_word_lbl.configure(text=f"Danger pool: {danger_pct}%")
        if word[-1] == self.forbidden:
            self._eliminate(self.bot_num,
                f"🤖 Bot played '{word}' — ends with forbidden '{self.forbidden}'! Bot is out.")
            return
        self.wordlist.append(word); self.wset.add(word)
        self.scores[self.bot_num - 1] += len(word); self.prevword = word
        self._set_msg(f"🤖 Bot played '{word}'  (+{len(word)} pts)", GLOW)
        self.current = self._next(); self._update_ui(); self._start_timer()

    # ── submit ────────────────────────────────────────────────────────────────
    def _submit(self):
        if self.current == self.bot_num: return
        raw = self._entry.get().strip().lower(); self._entry.delete(0, "end")
        if not raw: return
        p = self.current
        if raw == "/help":
            self._set_msg("/skip · /donate <pts> <p> · /wordlist · /help", ACCENT); return
        if raw == "/wordlist":
            self._set_msg("Used: " + ", ".join(self.wordlist), ACCENT); return
        if raw == "/skip":   self._do_skip(p); return
        if raw.startswith("/donate"): self._do_donate(p, raw); return
        if raw in self.wset:
            self._set_msg("Already used — pick a different word.", RED); return
        if dictionary_set and raw not in dictionary_set:
            self._set_msg(f'"{raw}" is not a valid English word.', RED); return
        if raw[0] != self.prevword[-1]:
            self._set_msg(f'Word must start with "{self.prevword[-1]}".', RED); return
        if raw[-1] == self.forbidden:
            self._eliminate(p, f"Player {p} is out! Word ended with forbidden '{self.forbidden}'."); return
        self.wordlist.append(raw); self.wset.add(raw)
        self.scores[p - 1] += len(raw); self.prevword = raw
        self._set_msg(f"Nice! +{len(raw)} pts for Player {p}.", GREEN)
        self.current = self._next(); self._update_ui()
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _do_skip(self, p):
        name = "🤖 Bot" if p == self.bot_num else f"Player {p}"
        o    = random.randint(0, 2)
        if o == 0:
            self.scores[p - 1] = max(0, self.scores[p - 1] - 10)
            self._set_msg(f"{name} skipped — lost 10 pts!", ORANGE)
        elif o == 1:
            self._set_msg(f"{name} skipped safely — no penalty.", GREEN)
        else:
            self._eliminate(p, f"{name} skipped and got eliminated!"); return
        self.current = self._next(); self._update_ui()
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _do_donate(self, p, raw):
        parts = raw.split()
        if len(parts) != 3: self._set_msg("/donate <pts> <player>", RED); return
        try: amt, target = int(parts[1]), int(parts[2])
        except ValueError: self._set_msg("/donate <pts> <player>", RED); return
        if amt <= 0 or target < 1 or target > self.n_players or target == p:
            self._set_msg("Invalid target.", RED); return
        if target not in self.active:
            tname = "🤖 Bot" if target == self.bot_num else f"Player {target}"
            self._set_msg(f"{tname} is already out.", RED); return
        actual = min(amt, self.scores[p - 1])
        self.scores[p - 1] -= actual; self.scores[target - 1] += actual
        tname = "🤖 Bot" if target == self.bot_num else f"Player {target}"
        self._set_msg(f"Player {p} donated {actual} pts to {tname}. Turn skipped.", ACCENT)
        self.current = self._next(); self._update_ui()
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)
        else: self._start_timer()

    def _eliminate(self, p, msg):
        next_p = self._next(); self.active.remove(p)
        self._set_msg(msg, RED_B if p == self.bot_num else ORANGE)
        self._update_ui()
        if len(self.active) == 1:
            if self._timer_id: self.after_cancel(self._timer_id); self._timer_id = None
            self.after(1400, lambda: self._end_game(self.active[0])); return
        self.current = next_p
        if self.current == self.bot_num: self.after(900, self._do_bot_turn)
        else: self.after(600, self._update_ui); self._start_timer()

    def _next(self):
        idx = self.active.index(self.current)
        return self.active[(idx + 1) % len(self.active)]

    # ── notepad ───────────────────────────────────────────────────────────────
    def _notepad_enter(self):
        raw = self._notepad_entry.get().strip().lower()
        self._notepad_entry.delete(0, "end")
        if not raw: self._notepad_entry.focus(); return
        if dictionary_set and raw not in dictionary_set:
            self._notepad_msg.configure(text=f'"{raw}" — not a word', text_color=RED)
            self.after(1500, lambda: self._notepad_msg.configure(text=""))
            self._notepad_entry.focus(); return
        self.notepad.append(raw)
        self._notepad_msg.configure(text=f'"{raw}" saved ✓', text_color=GREEN)
        self.after(1200, lambda: self._notepad_msg.configure(text=""))
        self._notepad_box.configure(state="normal")
        self._notepad_box.delete("1.0", "end")
        self._notepad_box.insert("end", "\n".join(self.notepad))
        self._notepad_box.configure(state="disabled")
        self._notepad_entry.focus()

    # ── end game ──────────────────────────────────────────────────────────────
    def _end_game(self, winner):
        self._clear()
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=60, pady=36)
        is_bot = winner == self.bot_num
        _lbl(root, "✦", size=52, color=ACCENT if not is_bot else GLOW).pack(pady=(0, 4))
        _lbl(root, "Game Over", size=26, weight="bold").pack()
        winner_txt = "🤖 Bot wins!" if is_bot else f"Player {winner} wins!"
        _lbl(root, winner_txt, size=15, weight="bold",
             color=GLOW if is_bot else ACCENT).pack(pady=(4, 16))

        card = _card(root); card.pack(fill="x", pady=(0, 20))
        _lbl(card, "Final Scores", size=12, color=DIM).pack(
            anchor="w", padx=20, pady=(14, 8))

        for i in sorted(range(1, self.n_players + 1),
                        key=lambda x: self.scores[x - 1], reverse=True):
            out  = i not in self.active; is_w = i == winner; ib = i == self.bot_num
            name = "🤖 Bot" if ib else f"Player {i}"
            col  = GLOW if (is_w and ib) else (ACCENT if is_w else (RED_B if out else DIM))
            row  = _card2(card); row.pack(fill="x", padx=16, pady=3)
            _lbl(row, name + (" · out" if out else "") + (" 🏆" if is_w else ""),
                 size=13, weight="bold" if is_w else "normal", color=col,
                 ).pack(side="left", padx=14, pady=10)
            _lbl(row, f"{self.scores[i - 1]} pts", size=13, color=col,
                 ).pack(side="right", padx=14)

        _lbl(card, f"Words played: {len(self.wordlist)}  ·  Final bot difficulty: {self.bot_diff}/100",
             size=11, color=DIM).pack(anchor="w", padx=20, pady=(4, 14))

        _btn_solid(root, "Play Again", self._show_lobby, height=46).pack(fill="x", pady=(0, 8))
        _btn(root, "⛶  Fullscreen", self._toggle_fs, color=DIM, height=36).pack(fill="x")


if __name__ == "__main__":
    app = ShiritoriBot()
    app.mainloop()