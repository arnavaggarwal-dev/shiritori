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
import com.shiritori.MainActivity
import org.json.JSONObject

/** Network game screen — receives state from server via GameClient. */
class NetGameFragment : Fragment() {

    // Root container — lets us swap content for disconnect screen
    private lateinit var container: FrameLayout

    // Game UI refs (non-null once game UI is built)
    private var turnLbl:      TextView? = null
    private var wordLbl:      TextView? = null
    private var hintLbl:      TextView? = null
    private var timerLbl:     TextView? = null
    private var forbLbl:      TextView? = null
    private var entry:        EditText? = null
    private var msgLbl:       TextView? = null
    private var chainLbl:     TextView? = null
    private var scoreBox:     LinearLayout? = null
    private val scoreLbls   = mutableMapOf<Int, Pair<TextView, TextView>>()
    private var playerNum:    Int? = null
    private var gameUiBuilt   = false

    private val handler = Handler(Looper.getMainLooper())

    // ── Lifecycle ──────────────────────────────────────────────────────────────
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx  = requireContext()
        this.container = FrameLayout(ctx).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT)
            setBackgroundColor(C_BG)
        }
        buildGameUi()
        return this.container
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        // Register as the active message + disconnect handler
        AppState.netMsgHandler = { msg -> if (isAdded) activity?.runOnUiThread { onMsg(msg) } }
        AppState.netDisconnectHandler = { if (isAdded) activity?.runOnUiThread { showDisconnect() } }
        // Drain any messages that arrived before this screen was shown
        while (AppState.pendingNetMsgs.isNotEmpty()) onMsg(AppState.pendingNetMsgs.removeFirst())
    }

    override fun onDestroyView() {
        super.onDestroyView()
        AppState.netMsgHandler       = null
        AppState.netDisconnectHandler= null
    }

    // ── Game UI ────────────────────────────────────────────────────────────────
    private fun buildGameUi() {
        val ctx = requireContext()
        val p = 14.dp(ctx)

        val root = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(C_BG)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT)
            setPadding(p, p, p, p)
        }

        // Header
        val hdr = ctx.card()
        val topRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = ctx.lp(mb = 2)
            gravity = Gravity.CENTER_VERTICAL
        }
        turnLbl = ctx.lbl("WAITING...", 12f, C_DIM, bold = true, wrap = true)
        turnLbl!!.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        timerLbl = ctx.lbl("--", 32f, C_ACCENT, bold = true, wrap = true)
        timerLbl!!.setShadowLayer(24f, 0f, 0f, C_ACCENT)
        timerLbl!!.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        topRow.addView(turnLbl); topRow.addView(timerLbl)
        hdr.addView(topRow)

        wordLbl = ctx.bigLbl("...", 42f, C_GLOW)
        hdr.addView(wordLbl)

        val hintRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = ctx.lp(mt = 4)
            gravity = Gravity.CENTER_VERTICAL
        }
        hintLbl = ctx.lbl("", 11f, C_DIM, wrap = true)
        hintLbl!!.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        forbLbl = ctx.lbl("", 11f, Color.WHITE, bold = true, wrap = true)
        forbLbl!!.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        forbLbl!!.background = roundedBg(Color.argb(200, 180, 30, 100), C_RED_B, 1, 20f, ctx)
        forbLbl!!.letterSpacing = 0.06f
        run { val h = 10.dp(ctx); val v = 4.dp(ctx); forbLbl!!.setPadding(h, v, h, v) }
        hintRow.addView(hintLbl); hintRow.addView(forbLbl)
        hdr.addView(hintRow)
        root.addView(hdr)

        // Input
        val inp = ctx.card()
        entry = ctx.textIn("TYPE YOUR WORD...") { submit() }; inp.addView(entry)
        val playRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; layoutParams = ctx.lp(h = 52.dp(ctx), mb = 4)
        }
        val bPlay = ctx.btnFilled("▶  PLAY", mb = 0) { submit() }
        (bPlay.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0; marginEnd = 6.dp(ctx) }
        val bSkip = ctx.btnOutline("SKIP", C_ORANGE, C_ORANGE, mb = 0) { send("/skip") }
        (bSkip.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0 }
        playRow.addView(bPlay); playRow.addView(bSkip)
        inp.addView(playRow)
        msgLbl = ctx.lbl("", 11f, C_DIM); inp.addView(msgLbl)
        root.addView(inp)

        // Middle: scores + chain (fills remaining space)
        val mid = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f
            ).also { it.bottomMargin = 10.dp(ctx) }
            background = roundedBg(C_CARD, C_BORDER, 1, 16f, ctx)
            setPadding(p, p, p, p)
        }
        scoreBox = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = ctx.lp()
        }
        scoreBox!!.addView(ctx.lbl("SCORES", 10f, C_ACCENT, bold = true))
        mid.addView(scoreBox)
        mid.addView(ctx.divider())
        mid.addView(ctx.lbl("CHAIN", 10f, C_DIM))
        mid.addView(ctx.space(2))
        chainLbl = ctx.lbl("", 10f, C_TEXT); mid.addView(chainLbl)
        root.addView(mid)

        root.addView(ctx.btnOutline("◀  QUIT", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        container.removeAllViews()
        container.addView(root)
        gameUiBuilt = true
    }

    // ── Message handler ────────────────────────────────────────────────────────
    fun onMsg(msg: JSONObject) {
        if (!isAdded) return
        when (msg.optString("type")) {
            "welcome" -> {
                playerNum         = msg.optInt("player_num")
                AppState.nPlayers = msg.optInt("num_players")
                turnLbl?.text     = "YOU ARE P$playerNum — WAITING..."
                rebuildScores(AppState.nPlayers)
            }
            "tick" -> {
                val tv = msg.optInt("time_left", 30)
                val tc = if (tv <= 10) C_RED_B else C_ACCENT
                timerLbl?.text = tv.toString()
                timerLbl?.setTextColor(tc)
                timerLbl?.setShadowLayer(24f, 0f, 0f, tc)
            }
            "game_start" -> applyState(msg)
            "state_update" -> {
                applyState(msg)
                val m = msg.optString("msg"); if (m.isNotEmpty()) setMsg(m, colorFor(msg.optString("color","dim")))
            }
            "msg" -> setMsg(msg.optString("text"), colorFor(msg.optString("color","dim")))
            "game_end" -> {
                applyState(msg)
                handler.postDelayed({ if (isAdded) endGame(msg.optInt("winner"), msg.optString("msg","")) }, 1000)
            }
        }
    }

    private fun applyState(msg: JSONObject) {
        if (!isAdded) return
        val cur    = msg.optInt("current_player", 1)
        val prev   = msg.optString("previous_word", "apple")
        val wlArr  = msg.optJSONArray("wordlist")
        val scArr  = msg.optJSONArray("scores")
        val actArr = msg.optJSONArray("active_players")
        val fb     = msg.optString("forbidden", "?")
        val n      = msg.optInt("num_players", AppState.nPlayers)

        val wl  = (0 until (wlArr?.length()  ?: 0)).map { wlArr!!.getString(it) }
        val sc  = (0 until (scArr?.length()  ?: 0)).map { scArr!!.getInt(it) }
        val act = (0 until (actArr?.length() ?: 0)).map { actArr!!.getInt(it) }

        AppState.netEndScores = sc; AppState.netActive = act
        AppState.netNPlayers  = n; AppState.netWordlist = wl

        val myTurn = cur == playerNum
        turnLbl?.text = if (myTurn) "YOUR TURN!" else "P${cur}'S TURN"
        turnLbl?.setTextColor(if (myTurn) C_ACCENT else C_DIM)
        wordLbl?.text = prev.uppercase()
        hintLbl?.text = "NEXT: \"${prev.last().uppercaseChar()}\""
        forbLbl?.text = "FORBID: ${fb.uppercase()}"
        entry?.isEnabled = myTurn
        chainLbl?.text = wl.takeLast(8).joinToString(" > ").uppercase()

        if (scoreLbls.isEmpty() && n > 0) rebuildScores(n)
        for (i in 1..n) {
            val out    = i !in act; val active = i == cur && !out
            val (nl, pl) = scoreLbls[i] ?: continue
            pl.text = sc.getOrNull(i - 1)?.toString() ?: "0"
            val you = if (i == playerNum) " (YOU)" else ""
            nl.text = "P$i$you" + (if (out) " [OUT]" else if (active) " ◀" else "")
            val col = when { out -> C_RED_B; active -> C_ACCENT; else -> C_DIM }
            nl.setTextColor(col); pl.setTextColor(col)
        }
    }

    private fun rebuildScores(n: Int) {
        if (!isAdded) return
        val ctx = requireContext()
        scoreBox?.removeAllViews()
        scoreBox?.addView(ctx.lbl("SCORES", 10f, C_ACCENT, bold = true))
        scoreBox?.addView(ctx.space(4))
        scoreLbls.clear()
        for (i in 1..n) {
            val row = LinearLayout(ctx).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, 30.dp(ctx))
            }
            val you = if (i == playerNum) " (YOU)" else ""
            val nl = ctx.lbl("P$i$you", 13f, C_TEXT, wrap = true)
            nl.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            val pl = ctx.lbl("0", 13f, C_ACCENT, bold = true, wrap = true)
            pl.layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            row.addView(nl); row.addView(pl); scoreBox?.addView(row)
            scoreLbls[i] = nl to pl
        }
    }

    private fun setMsg(text: String, color: Int = C_DIM) {
        if (!isAdded) return; msgLbl?.text = text; msgLbl?.setTextColor(color)
    }

    private fun submit() {
        val raw = entry?.text?.toString()?.trim()?.lowercase() ?: return
        entry?.setText("")
        if (raw.isEmpty() || entry?.isEnabled == false) return
        when {
            raw == "/help"     -> { setMsg("/SKIP  /DONATE <PTS> <P>  /WORDLIST", C_ACCENT); return }
            raw == "/wordlist" -> { setMsg("SEE CHAIN ABOVE.", C_ACCENT); return }
        }
        send(raw)
    }

    private fun send(word: String) { AppState.client?.sendAction(word) }

    fun showDisconnect() {
        if (!isAdded) return
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()
        root.addView(ctx.space(40))
        root.addView(ctx.bigLbl("!! DISCONNECTED !!", 16f, C_RED_B))
        root.addView(ctx.lbl("CONNECTION TO HOST WAS LOST.", 12f, C_DIM, gravity = android.view.Gravity.CENTER))
        root.addView(ctx.space(20))
        root.addView(ctx.btnFilled("◀  BACK TO LOBBY") { (activity as? MainActivity)?.navigateToLobby() })
        container.removeAllViews()
        container.addView(sv)
    }

    // Keep `_onDisconnect` as a public alias (called by older code paths)
    fun _onDisconnect() = showDisconnect()

    private fun endGame(winner: Int, extraMsg: String) {
        AppState.winner    = winner; AppState.endMsg = extraMsg
        AppState.scores    = AppState.netEndScores.toMutableList()
        AppState.active    = AppState.netActive.toMutableList()
        AppState.nPlayers  = AppState.netNPlayers
        AppState.wordlist  = AppState.netWordlist.toMutableList()
        AppState.playerNum = playerNum
        (activity as? MainActivity)?.navigate(EndFragment())
    }
}
