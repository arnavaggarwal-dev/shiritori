# pip install customtkinter
import customtkinter as ctk
import random
import json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

try:
    with open("words_dictionary.json", "r") as f:
        dictionary = set(json.load(f).keys())
except FileNotFoundError:
    dictionary = set()
    print("Warning: words_dictionary.json not found. Word validation disabled.")

# ── colours ──────────────────────────────────────────────────────────────────
ACCENT  = "#5B8DEF"
RED     = "#E24B4A"
GREEN   = "#5a9e3a"
ORANGE  = "#E9930A"
GRAY_FG = ("gray90", "gray20")
CARD_FG = ("white",  "gray17")


class ShiritoriApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shiritori")
        self.geometry("720x620")
        self.resizable(True, True)
        self.minsize(640, 540)

        self._fullscreen = False
        self.bind("<F11>",    lambda e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._exit_fullscreen())

        self.num_players    = 2
        self.scores         = []
        self.active_players = []
        self.wordlist       = []
        self.forbidden      = ""
        self.current_player = 1
        self.previous_word  = ""

        self._show_setup()

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        if hasattr(self, "_fs_btn"):
            self._fs_btn.configure(text="Exit fullscreen  ⛶" if self._fullscreen else "Fullscreen  ⛶")

    def _exit_fullscreen(self):
        if self._fullscreen:
            self._fullscreen = False
            self.attributes("-fullscreen", False)
            if hasattr(self, "_fs_btn"):
                self._fs_btn.configure(text="Fullscreen  ⛶")

    # ── helpers ───────────────────────────────────────────────────────────────
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, corner_radius=14, fg_color=CARD_FG, **kw)

    def _label(self, parent, text, size=13, weight="normal", color=None, **kw):
        font = ctk.CTkFont(size=size, weight=weight)
        args = dict(text=text, font=font, **kw)
        if color:
            args["text_color"] = color
        return ctk.CTkLabel(parent, **args)

    def _set_message(self, text, color):
        self._msg_label.configure(text=text, text_color=color)

    def _change_player(self):
        idx = self.active_players.index(self.current_player)
        return self.active_players[(idx + 1) % len(self.active_players)]

    # ── setup screen ──────────────────────────────────────────────────────────
    def _show_setup(self):
        self._clear()

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=56, pady=48)

        self._label(root, "SHIRITORI", size=38, weight="bold", color=ACCENT).pack()
        self._label(root, "The traditional Japanese word chaining game",
                    size=13, color="gray").pack(pady=(2, 28))

        card = self._card(root)
        card.pack(fill="x", pady=(0, 20))

        self._label(card, "Number of players", size=12, color="gray").pack(
            anchor="w", padx=24, pady=(20, 6))

        self._player_var = ctk.IntVar(value=2)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(0, 4))

        self._slider_lbl = self._label(row, "2 players", size=13, weight="bold", width=78)

        ctk.CTkSlider(
            row, from_=2, to=8, number_of_steps=6,
            variable=self._player_var,
            command=lambda v: self._slider_lbl.configure(text=f"{int(v)} players")
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._slider_lbl.pack(side="left")

        rules_frame = ctk.CTkFrame(card, fg_color=GRAY_FG, corner_radius=10)
        rules_frame.pack(fill="x", padx=24, pady=(12, 20))

        for rule in [
            "Chain words by the last letter of the previous word",
            "No word may be repeated",
            "Must be a real English word",
            "Ending on the forbidden letter gets you eliminated",
        ]:
            r = ctk.CTkFrame(rules_frame, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=2)
            self._label(r, "·", size=14, color=ACCENT).pack(side="left", padx=(0, 8))
            self._label(r, rule, size=12, color="gray").pack(side="left", pady=4)

        ctk.CTkButton(
            root, text="Start Game", font=ctk.CTkFont(size=15, weight="bold"),
            height=46, corner_radius=12, command=self._start_game
        ).pack(fill="x", pady=(0, 8))

        self._fs_btn = ctk.CTkButton(
            root, text="Fullscreen  ⛶",
            font=ctk.CTkFont(size=13), height=36, corner_radius=12,
            fg_color="transparent", border_width=1,
            command=self._toggle_fullscreen
        )
        self._fs_btn.pack(fill="x")

    def _start_game(self):
        self.num_players    = int(self._player_var.get())
        self.scores         = [0] * self.num_players
        self.active_players = list(range(1, self.num_players + 1))
        self.wordlist       = ["apple"]
        self.forbidden      = chr(random.randint(ord("a"), ord("z")))
        self.current_player = 1
        self.previous_word  = "apple"
        self._show_game()

    # ── game screen ───────────────────────────────────────────────────────────
    def _show_game(self):
        self._clear()

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        # ── left column ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # header card: current word + forbidden badge
        header = self._card(left)
        header.pack(fill="x", pady=(0, 10))
        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(18, 0))

        word_col = ctk.CTkFrame(top_row, fg_color="transparent")
        word_col.pack(side="left", fill="x", expand=True)

        self._turn_lbl = self._label(word_col, "", size=12, color="gray")
        self._turn_lbl.pack(anchor="w")
        self._word_lbl = self._label(word_col, "", size=36, weight="bold")
        self._word_lbl.pack(anchor="w", pady=(2, 0))

        badge = ctk.CTkFrame(top_row, fg_color=("#3d1010", "#3d1010"), corner_radius=10)
        badge.pack(side="right", padx=(8, 0))
        self._label(badge, "forbidden", size=10, color=RED).pack(padx=14, pady=(8, 0))
        self._forbidden_lbl = self._label(
            badge, self.forbidden.upper(), size=26, weight="bold", color=RED)
        self._forbidden_lbl.pack(padx=14, pady=(0, 8))

        self._hint_lbl = self._label(header, "", size=12, color="gray")
        self._hint_lbl.pack(anchor="w", padx=20, pady=(4, 16))

        # input card
        inp_card = self._card(left)
        inp_card.pack(fill="x", pady=(0, 10))

        self._entry = ctk.CTkEntry(
            inp_card, placeholder_text="Type your word and press Enter…",
            font=ctk.CTkFont(size=14), height=46, corner_radius=10)
        self._entry.pack(fill="x", padx=16, pady=(16, 8))
        self._entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inp_card, text="Play Word",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40, corner_radius=10, command=self._submit
        ).pack(fill="x", padx=16, pady=(0, 8))

        self._msg_label = self._label(inp_card, "", size=12, wraplength=360)
        self._msg_label.pack(padx=16, pady=(0, 14))

        # word chain card
        chain_card = self._card(left)
        chain_card.pack(fill="both", expand=True)

        ch_row = ctk.CTkFrame(chain_card, fg_color="transparent")
        ch_row.pack(fill="x", padx=16, pady=(12, 4))
        self._label(ch_row, "Word chain", size=12, color="gray").pack(side="left")
        self._chain_cnt = self._label(ch_row, "1", size=12, weight="bold", color=ACCENT)
        self._chain_cnt.pack(side="right")

        self._chain_box = ctk.CTkTextbox(
            chain_card, font=ctk.CTkFont(size=12),
            activate_scrollbars=True, wrap="word")
        self._chain_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self._chain_box.configure(state="disabled")

        # ── right column: scores ─────────────────────────────────────────────
        right = self._card(outer)
        right.configure(width=190)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._label(right, "Scores", size=13, weight="bold").pack(
            padx=16, pady=(18, 10))

        self._score_cards        = {}
        self._score_labels       = {}
        self._player_name_labels = {}

        for i in range(1, self.num_players + 1):
            f = ctk.CTkFrame(right, corner_radius=10, fg_color=GRAY_FG)
            f.pack(fill="x", padx=12, pady=3)
            name_lbl = self._label(f, f"Player {i}", size=12)
            name_lbl.pack(side="left", padx=(12, 4), pady=10)
            pts_lbl = self._label(f, "0", size=13, weight="bold")
            pts_lbl.pack(side="right", padx=12)
            self._score_cards[i]         = f
            self._score_labels[i]        = pts_lbl
            self._player_name_labels[i]  = name_lbl

        sep = ctk.CTkFrame(right, height=1, fg_color=GRAY_FG)
        sep.pack(fill="x", padx=16, pady=(16, 8))
        self._label(right, "commands", size=11, color="gray").pack()
        for cmd in ["/help", "/rules", "/wordlist", "/skip", "/donate <pts> <p>"]:
            self._label(right, cmd, size=11, color=ACCENT).pack(pady=1)

        # fullscreen toggle button at bottom of right panel
        ctk.CTkFrame(right, height=1, fg_color=GRAY_FG).pack(fill="x", padx=16, pady=(12, 8))
        self._fs_btn = ctk.CTkButton(
            right, text="Fullscreen  ⛶",
            font=ctk.CTkFont(size=11), height=30, corner_radius=8,
            fg_color="transparent", border_width=1,
            command=self._toggle_fullscreen
        )
        self._fs_btn.pack(fill="x", padx=12, pady=(0, 12))

        self._entry.focus()
        self._update_ui()

    def _update_ui(self):
        w    = self.previous_word
        last = w[-1]

        self._turn_lbl.configure(text=f"Player {self.current_player}'s turn")
        self._word_lbl.configure(text=w)
        self._hint_lbl.configure(text=f'Next word must start with  "{last}"')
        self._forbidden_lbl.configure(text=self.forbidden.upper())

        self._chain_box.configure(state="normal")
        self._chain_box.delete("1.0", "end")
        self._chain_box.insert("end", "  →  ".join(self.wordlist))
        self._chain_box.configure(state="disabled")
        self._chain_cnt.configure(text=str(len(self.wordlist)))

        for i in range(1, self.num_players + 1):
            out    = i not in self.active_players
            active = (i == self.current_player) and not out
            self._score_labels[i].configure(text=str(self.scores[i - 1]))
            if out:
                self._score_cards[i].configure(fg_color=("gray80", "gray28"))
                self._score_labels[i].configure(text_color="gray")
                self._player_name_labels[i].configure(text_color="gray")
            elif active:
                self._score_cards[i].configure(fg_color=("#1a3566", "#1a3566"))
                self._score_labels[i].configure(text_color=ACCENT)
                self._player_name_labels[i].configure(text_color="white")
            else:
                self._score_cards[i].configure(fg_color=GRAY_FG)
                self._score_labels[i].configure(text_color=("gray20", "gray80"))
                self._player_name_labels[i].configure(text_color=("gray30", "gray70"))

    # ── game logic ────────────────────────────────────────────────────────────
    def _submit(self):
        raw = self._entry.get().strip().lower()
        self._entry.delete(0, "end")
        if not raw:
            return

        if raw.startswith("/"):
            self._handle_command(raw)
            return

        if raw in self.wordlist:
            self._set_message("Already used — pick a different word.", RED)
            return

        if dictionary and raw not in dictionary:
            self._set_message(f'"{raw}" is not a valid English word.', RED)
            return

        if raw[0] != self.previous_word[-1]:
            self._set_message(
                f'Word must start with "{self.previous_word[-1]}".', RED)
            return

        if raw[-1] == self.forbidden:
            next_p = self._change_player()
            self.active_players.remove(self.current_player)
            self._set_message(
                f"Player {self.current_player} is out! "
                f'Word ended with the forbidden letter "{self.forbidden}".', ORANGE)
            self._update_ui()
            if len(self.active_players) == 1:
                self.after(1400, self._show_end)
                return
            self.current_player = next_p
            self.after(1000, self._update_ui)
            return

        self.wordlist.append(raw)
        self.scores[self.current_player - 1] += len(raw)
        self.previous_word  = raw
        self._set_message(f"Nice! +{len(raw)} pts for Player {self.current_player}.", GREEN)
        self.current_player = self._change_player()
        self._update_ui()

    def _handle_command(self, cmd):
        parts = cmd.split()

        if cmd == "/help":
            self._set_message(
                "Commands: /rules · /wordlist · /skip · /donate <pts> <player> · /help", ACCENT)

        elif cmd == "/rules":
            self._set_message(
                f"Chain words by last letter. No repeats. "
                f'Real words only. Forbidden: "{self.forbidden}".', ACCENT)

        elif cmd == "/wordlist":
            self._set_message("Used: " + ", ".join(self.wordlist), ACCENT)

        elif cmd == "/skip":
            outcome = random.randint(0, 2)
            if outcome == 0:
                # -10 pts
                self.scores[self.current_player - 1] = max(
                    0, self.scores[self.current_player - 1] - 10)
                self._set_message(
                    f"Player {self.current_player} skipped — lost 10 pts!", ORANGE)
                self.current_player = self._change_player()
                self._update_ui()
            elif outcome == 1:
                # 0 pts — safe skip
                self._set_message(
                    f"Player {self.current_player} skipped — no penalty this time.", GREEN)
                self.current_player = self._change_player()
                self._update_ui()
            else:
                # eliminated
                next_p = self._change_player()
                self.active_players.remove(self.current_player)
                self._set_message(
                    f"Player {self.current_player} skipped and got eliminated! Bad luck.", RED)
                self._update_ui()
                if len(self.active_players) == 1:
                    self.after(1400, self._show_end)
                    return
                self.current_player = next_p
                self.after(1000, self._update_ui)

        elif parts[0] == "/donate":
            if len(parts) != 3:
                self._set_message("Usage: /donate <pts> <player number>", RED)
                return
            try:
                amt    = int(parts[1])
                target = int(parts[2])
            except ValueError:
                self._set_message("Usage: /donate <pts> <player number>", RED)
                return
            if amt <= 0:
                self._set_message("Donation amount must be positive.", RED)
                return
            if target < 1 or target > self.num_players:
                self._set_message(f"Player {target} does not exist.", RED)
                return
            if target == self.current_player:
                self._set_message("You can't donate to yourself.", RED)
                return
            if target not in self.active_players:
                self._set_message(f"Player {target} is already out.", RED)
                return
            actual = min(amt, self.scores[self.current_player - 1])
            self.scores[self.current_player - 1] -= actual
            self.scores[target - 1]              += actual
            self._set_message(
                f"Player {self.current_player} donated {actual} pts to Player {target}. Turn skipped.", ACCENT)
            self.current_player = self._change_player()
            self._update_ui()

        else:
            self._set_message(f"Unknown command: {cmd}", RED)

    # ── end screen ────────────────────────────────────────────────────────────
    def _show_end(self):
        self._clear()

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=56, pady=40)

        winner = self.active_players[0]

        self._label(root, "🏆", size=52).pack(pady=(0, 6))
        self._label(root, "Game Over", size=30, weight="bold").pack()
        self._label(root, f"Player {winner} wins!", size=16, color=ACCENT).pack(pady=(4, 24))

        card = self._card(root)
        card.pack(fill="x", pady=(0, 20))

        self._label(card, "Final scores", size=12, color="gray").pack(
            anchor="w", padx=20, pady=(16, 8))

        for i in sorted(range(1, self.num_players + 1),
                        key=lambda x: self.scores[x - 1], reverse=True):
            out  = i not in self.active_players
            is_w = i == winner
            row  = ctk.CTkFrame(
                card, corner_radius=10,
                fg_color=("gray85", "gray25") if out else CARD_FG)
            row.pack(fill="x", padx=16, pady=3)

            label_txt = f"Player {i}" + (" (OUT)" if out else "") + (" 🏆" if is_w else "")
            self._label(
                row, label_txt, size=13,
                weight="bold" if is_w else "normal",
                color="gray" if out else ("gray10", "gray90")
            ).pack(side="left", padx=14, pady=10)

            self._label(
                row, f"{self.scores[i - 1]} pts", size=13,
                color="gray" if out else ACCENT
            ).pack(side="right", padx=14)

        self._label(card, f"Total words played: {len(self.wordlist)}",
                    size=12, color="gray").pack(anchor="w", padx=20, pady=(6, 16))

        ctk.CTkButton(
            root, text="Play Again",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46, corner_radius=12, command=self._show_setup
        ).pack(fill="x", pady=(0, 8))

        self._fs_btn = ctk.CTkButton(
            root, text="Fullscreen  ⛶",
            font=ctk.CTkFont(size=13), height=36, corner_radius=12,
            fg_color="transparent", border_width=1,
            command=self._toggle_fullscreen
        )
        self._fs_btn.pack(fill="x")


if __name__ == "__main__":
    app = ShiritoriApp()
    app.mainloop()