package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.MainActivity

class EndFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val a   = AppState
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("GAME OVER", 24f, C_RED_B))
        root.addView(ctx.space(8))

        val winner = a.winner
        val isBot  = winner == a.botNum
        val isMe   = winner == a.playerNum
        val wtxt   = when { isBot -> "[BOT] WINS!"; isMe -> "P$winner WINS!  —  YOU!"; else -> "P$winner WINS!" }
        root.addView(ctx.bigLbl(wtxt, 16f, if (isBot) C_PURPLE else C_ACCENT))
        root.addView(ctx.space(12))

        if (a.endMsg.isNotBlank()) {
            root.addView(ctx.lbl(a.endMsg.take(80), 11f, C_DIM, gravity = android.view.Gravity.CENTER))
            root.addView(ctx.space(8))
        }

        val card = ctx.card()
        card.addView(ctx.lbl("FINAL SCORES", 11f, C_DIM, bold = true))

        val scores  = a.scores
        val active  = a.active
        val n       = a.nPlayers
        val botNum  = a.botNum
        val playerN = a.playerNum

        // Sort by score descending
        (1..n).sortedByDescending { scores.getOrNull(it - 1) ?: 0 }.forEach { i ->
            val out  = i !in active
            val isW  = i == winner
            val isB  = i == botNum
            val name = when { isB -> "[BOT]"; playerN != null && i == playerN -> "P$i (YOU)"; else -> "P$i" }
            val col  = when { isW && isB -> C_PURPLE; isW -> C_ACCENT; out -> C_RED_B; else -> C_DIM }
            val suffix = (if (out) " [OUT]" else "") + (if (isW) " 🏆" else "")
            val row  = LinearLayout(ctx).apply {
                orientation = LinearLayout.HORIZONTAL; layoutParams = ctx.lp(h = 30.dp(ctx))
            }
            val nl = ctx.lbl(name + suffix, 12f, col, bold = isW, wrap = true)
            nl.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            val sc  = scores.getOrNull(i - 1) ?: 0
            val pl  = ctx.lbl("$sc PTS", 12f, col, wrap = true)
            row.addView(nl); row.addView(pl); card.addView(row)
        }

        card.addView(ctx.space(6))
        card.addView(ctx.lbl("WORDS PLAYED: ${a.wordlist.size}", 10f, C_DIM))
        if (a.gameMode == "bot") card.addView(ctx.lbl("FINAL BOT DIFF: ${a.botDiff}/100", 10f, C_DIM))
        root.addView(card)

        root.addView(ctx.space(10))
        root.addView(ctx.btnFilled("▶  PLAY AGAIN") { (activity as? MainActivity)?.navigateToLobby() })

        return sv
    }
}
