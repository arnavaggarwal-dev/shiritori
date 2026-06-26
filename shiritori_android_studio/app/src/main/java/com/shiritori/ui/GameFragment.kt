package com.shiritori.ui

import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.GameLogic
import com.shiritori.MainActivity

/** Handles both local (pass-and-play) and bot game modes. */
class GameFragment : Fragment() {

    // ── UI refs ────────────────────────────────────────────────────────────────
    private lateinit var turnLbl:    TextView
    private lateinit var wordLbl:    TextView
    private lateinit var hintLbl:    TextView
    private lateinit var timerLbl:   TextView
    private lateinit var forbLbl:    TextView
    private lateinit var entry:      EditText
    private lateinit var msgLbl:     TextView
    private lateinit var chainLbl:   TextView
    private val scoreLbls = mutableMapOf<Int, Pair<TextView, TextView>>()
    private var diffLbl:    TextView? = null
    private var diffSlider: SeekBar?  = null

    // ── Timer ──────────────────────────────────────────────────────────────────
    private val handler = Handler(Looper.getMainLooper())
    private val tickRunnable = object : Runnable {
        override fun run() { if (isAdded) tick() }
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────────
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View =
        buildUi()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        updateUi()
        startTimer()
        if (AppState.gameMode == "bot" && AppState.current == AppState.botNum)
            handler.postDelayed({ if (isAdded) doBotTurn() }, 1000)
    }

    override fun onDestroyView() { super.onDestroyView(); cancelTimer() }

    // ── UI builder ─────────────────────────────────────────────────────────────
    private fun buildUi(): View {
        val ctx = requireContext()
        val p = 14.dp(ctx)

        val root = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(C_BG)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT)
            setPadding(p, p, p, p)
        }

        // ── Header ──────────────────────────────────────────────────────────
        val hdr = ctx.card()

        val topRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = ctx.lp(mb = 2)
            gravity = Gravity.CENTER_VERTICAL
        }
        turnLbl = ctx.lbl("", 12f, C_ACCENT, bold = true, wrap = true)
        turnLbl.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        timerLbl = ctx.lbl("30", 32f, C_ACCENT, bold = true, wrap = true)
        timerLbl.setShadowLayer(24f, 0f, 0f, C_ACCENT)
        timerLbl.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        topRow.addView(turnLbl); topRow.addView(timerLbl)
        hdr.addView(topRow)

        wordLbl = ctx.bigLbl("", 42f, C_GLOW)
        hdr.addView(wordLbl)

        val hintRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = ctx.lp(mt = 4)
            gravity = Gravity.CENTER_VERTICAL
        }
        hintLbl = ctx.lbl("", 11f, C_DIM, wrap = true)
        hintLbl.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        forbLbl = ctx.lbl("", 11f, Color.WHITE, bold = true, wrap = true)
        forbLbl.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        forbLbl.background = roundedBg(Color.argb(200, 180, 30, 100), C_RED_B, 1, 20f, ctx)
        forbLbl.letterSpacing = 0.06f
        run { val h = 10.dp(ctx); val v = 4.dp(ctx); forbLbl.setPadding(h, v, h, v) }
        hintRow.addView(hintLbl); hintRow.addView(forbLbl)
        hdr.addView(hintRow)

        if (AppState.gameMode == "bot") {
            diffLbl = ctx.lbl("BOT: ${AppState.botDiff}/100", 10f, C_PURPLE)
            diffLbl!!.layoutParams = ctx.lp(mt = 2)
            hdr.addView(diffLbl)
        }
        root.addView(hdr)

        // ── Input ────────────────────────────────────────────────────────────
        val inp = ctx.card()
        entry = ctx.textIn("TYPE YOUR WORD...") { submit() }
        inp.addView(entry)
        val playRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; layoutParams = ctx.lp(h = 52.dp(ctx), mb = 4)
        }
        val bPlay = ctx.btnFilled("▶  PLAY", mb = 0) { submit() }
        (bPlay.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0; marginEnd = 6.dp(ctx) }
        val bSkip = ctx.btnOutline("SKIP", C_ORANGE, C_ORANGE, mb = 0) { doSkip(AppState.current) }
        (bSkip.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0 }
        playRow.addView(bPlay); playRow.addView(bSkip)
        inp.addView(playRow)
        msgLbl = ctx.lbl("", 11f, C_DIM); inp.addView(msgLbl)
        root.addView(inp)

        // ── Middle: scores + chain (fills remaining space) ───────────────────
        val mid = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f
            ).also { it.bottomMargin = 10.dp(ctx) }
            background = roundedBg(C_CARD, C_BORDER, 1, 16f, ctx)
            setPadding(p, p, p, p)
        }
        mid.addView(ctx.lbl("SCORES", 10f, C_ACCENT, bold = true))
        mid.addView(ctx.space(4))
        for (i in 1..AppState.nPlayers) {
            val isBot = i == AppState.botNum
            val row = LinearLayout(ctx).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, 30.dp(ctx))
            }
            val nl = ctx.lbl(if (isBot) "[BOT]" else "P$i", 13f, if (isBot) C_PURPLE else C_TEXT, wrap = true)
            nl.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            val pl = ctx.lbl("0", 13f, if (isBot) C_PURPLE else C_ACCENT, bold = true, wrap = true)
            pl.layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            row.addView(nl); row.addView(pl)
            mid.addView(row)
            scoreLbls[i] = nl to pl
        }
        mid.addView(ctx.divider())
        mid.addView(ctx.lbl("CHAIN", 10f, C_DIM))
        mid.addView(ctx.space(2))
        chainLbl = ctx.lbl("", 10f, C_TEXT); mid.addView(chainLbl)
        root.addView(mid)

        // ── Footer ───────────────────────────────────────────────────────────
        if (AppState.gameMode == "bot") {
            val ds = ctx.card()
            ds.addView(ctx.lbl("BOT DIFFICULTY (LIVE)", 10f, C_PURPLE))
            diffSlider = SeekBar(ctx).apply {
                max = 99; progress = AppState.botDiff - 1
                layoutParams = ctx.lp(h = 36.dp(ctx))
                setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                    override fun onProgressChanged(s: SeekBar, p: Int, fromUser: Boolean) {
                        AppState.botDiff = p + 1; diffLbl?.text = "BOT: ${p+1}/100"
                    }
                    override fun onStartTrackingTouch(s: SeekBar) {}
                    override fun onStopTrackingTouch(s: SeekBar) {}
                })
            }
            ds.addView(diffSlider)
            root.addView(ds)
        }

        root.addView(ctx.btnOutline("◀  QUIT", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return root
    }

    // ── UI update ──────────────────────────────────────────────────────────────
    private fun updateUi() {
        if (!isAdded) return
        val a = AppState
        val isBot = a.gameMode == "bot" && a.current == a.botNum
        turnLbl.text = if (isBot) "[BOT] THINKING..." else "P${a.current}'S TURN"
        turnLbl.setTextColor(if (isBot) C_PURPLE else C_ACCENT)
        wordLbl.text = a.prevword.uppercase()
        hintLbl.text = "NEXT: \"${a.prevword.last().uppercaseChar()}\""
        forbLbl.text = "FORBID: ${a.forbidden.uppercaseChar()}"
        entry.isEnabled = !isBot
        chainLbl.text = a.wordlist.takeLast(8).joinToString(" > ").uppercase()

        for (i in 1..a.nPlayers) {
            val out    = i !in a.active
            val active = i == a.current && !out
            val isB    = i == a.botNum
            val (nl, pl) = scoreLbls[i] ?: continue
            pl.text = a.scores.getOrNull(i - 1)?.toString() ?: "0"
            val suffix = if (out) " [OUT]" else if (active) " ◀" else ""
            nl.text = (if (isB) "[BOT]" else "P$i") + suffix
            val col = when { out -> C_RED_B; active -> if (isB) C_PURPLE else C_ACCENT; else -> C_DIM }
            nl.setTextColor(col); pl.setTextColor(col)
        }
    }

    private fun setMsg(text: String, color: Int = C_DIM) {
        if (!isAdded) return
        msgLbl.text = text; msgLbl.setTextColor(color)
    }

    // ── Timer ──────────────────────────────────────────────────────────────────
    private fun startTimer() {
        cancelTimer(); AppState.timeLeft = 30
        handler.postDelayed(tickRunnable, 1000)
    }

    private fun cancelTimer() { handler.removeCallbacks(tickRunnable) }

    private fun tick() {
        AppState.timeLeft--; val t = AppState.timeLeft
        val tc = if (t <= 10) C_RED_B else C_ACCENT
        timerLbl.text = t.toString()
        timerLbl.setTextColor(tc)
        timerLbl.setShadowLayer(24f, 0f, 0f, tc)
        if (t <= 0) {
            if (AppState.gameMode != "bot" || AppState.current != AppState.botNum) doSkip(AppState.current)
            return
        }
        handler.postDelayed(tickRunnable, 1000)
    }

    // ── Game logic ─────────────────────────────────────────────────────────────
    private fun submit() {
        val raw = entry.text.toString().trim().lowercase(); entry.setText("")
        if (raw.isEmpty()) return
        val a = AppState
        if (a.gameMode == "bot" && a.current == a.botNum) return
        when {
            raw == "/help"     -> { setMsg("/SKIP  /DONATE <PTS> <P>  /WORDLIST", C_ACCENT); return }
            raw == "/wordlist" -> { setMsg("USED: " + a.wordlist.takeLast(5).joinToString(" ").uppercase(), C_ACCENT); return }
            raw == "/skip"     -> { doSkip(a.current); return }
            raw.startsWith("/donate") -> { donate(a.current, raw); return }
        }
        processWord(a.current, raw)
    }

    private fun processWord(p: Int, word: String) {
        val a = AppState
        when {
            word in a.wset -> { setMsg("ALREADY USED.", C_RED_B); return }
            GameLogic.dictionarySet.isNotEmpty() && word !in GameLogic.dictionarySet -> { setMsg("\"${word.uppercase()}\" NOT A WORD.", C_RED_B); return }
            word[0] != a.prevword.last() -> { setMsg("MUST START WITH \"${a.prevword.last().uppercaseChar()}\".", C_RED_B); return }
            word.last() == a.forbidden   -> { eliminate(p, "P$p OUT! ENDED WITH '${a.forbidden.uppercaseChar()}'."); return }
        }
        a.wordlist.add(word); a.wset.add(word); a.scores[p - 1] += word.length; a.prevword = word
        setMsg("+${word.length} PTS FOR P$p.", C_GREEN)
        a.current = next(); updateUi(); startTimer()
        if (a.gameMode == "bot" && a.current == a.botNum)
            handler.postDelayed({ if (isAdded) doBotTurn() }, 1000)
    }

    private fun doSkip(p: Int) {
        val a = AppState; val name = if (p == a.botNum) "[BOT]" else "P$p"
        when ((0..2).random()) {
            0 -> { a.scores[p - 1] = maxOf(0, a.scores[p - 1] - 10); setMsg("$name SKIPPED. -10 PTS.", C_ORANGE) }
            1 -> setMsg("$name SKIPPED SAFELY.", C_GREEN)
            else -> { eliminate(p, "$name ELIMINATED!"); return }
        }
        a.current = next(); updateUi(); startTimer()
        if (a.gameMode == "bot" && a.current == a.botNum)
            handler.postDelayed({ if (isAdded) doBotTurn() }, 1000)
    }

    private fun donate(p: Int, raw: String) {
        val a = AppState; val parts = raw.split(" ")
        if (parts.size != 3) { setMsg("/DONATE <PTS> <PLAYER>", C_RED_B); return }
        val amt    = parts[1].toIntOrNull() ?: run { setMsg("INVALID.", C_RED_B); return }
        val target = parts[2].toIntOrNull() ?: run { setMsg("INVALID.", C_RED_B); return }
        if (amt <= 0 || target < 1 || target > a.nPlayers || target == p || target !in a.active) { setMsg("INVALID.", C_RED_B); return }
        val actual = minOf(amt, a.scores[p - 1])
        a.scores[p - 1] -= actual; a.scores[target - 1] += actual
        val tn = if (target == a.botNum) "[BOT]" else "P$target"
        setMsg("P$p DONATED $actual TO $tn.", C_ACCENT)
        a.current = next(); updateUi(); startTimer()
        if (a.gameMode == "bot" && a.current == a.botNum)
            handler.postDelayed({ if (isAdded) doBotTurn() }, 1000)
    }

    private fun eliminate(p: Int, msg: String) {
        val a = AppState; val nextP = next(); a.active.remove(p)
        setMsg(msg, if (p == a.botNum) C_GLOW else C_RED_B); updateUi()
        if (a.active.size == 1) {
            cancelTimer()
            handler.postDelayed({ if (isAdded) endGame(a.active[0]) }, 1400); return
        }
        a.current = nextP; updateUi(); startTimer()
        if (a.gameMode == "bot" && a.current == a.botNum)
            handler.postDelayed({ if (isAdded) doBotTurn() }, 1000)
    }

    private fun doBotTurn() {
        val a = AppState; if (a.current != a.botNum) return
        val word = GameLogic.botPick(a.prevword.last(), a.wset, a.forbidden, a.botDiff)
        if (word == null) { doSkip(a.botNum!!); return }
        if (word.last() == a.forbidden) { eliminate(a.botNum!!, "[BOT] '${word.uppercase()}' ENDS WITH FORBIDDEN!"); return }
        a.wordlist.add(word); a.wset.add(word); a.scores[a.botNum!! - 1] += word.length; a.prevword = word
        setMsg("[BOT] '${word.uppercase()}' +${word.length}", C_PURPLE)
        a.current = next(); updateUi(); startTimer()
    }

    private fun next(): Int {
        val a = AppState; val idx = a.active.indexOf(a.current)
        return a.active[(idx + 1) % a.active.size]
    }

    // ── End ────────────────────────────────────────────────────────────────────
    private fun endGame(winner: Int) {
        AppState.winner = winner
        (activity as? MainActivity)?.navigate(EndFragment())
    }
}
