package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.GameLogic
import com.shiritori.MainActivity

class BotSetupFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("BOT MODE", 20f, C_PURPLE))
        root.addView(ctx.space(16))

        // Human players
        val pc = ctx.card()
        pc.addView(ctx.lbl("HUMAN PLAYERS", 12f, C_DIM))
        val pLbl: TextView = ctx.lbl("1 PLAYER", 13f, C_ACCENT, bold = true)
        pc.addView(pLbl)
        val pSlider = SeekBar(ctx).apply {
            max = 6; progress = 0          // 1..7
            layoutParams = ctx.lp(h = 44.dp(ctx), mb = 4)
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar, p: Int, fromUser: Boolean) {
                    val n = p + 1; pLbl.text = "$n PLAYER${if (n > 1) "S" else ""}"
                }
                override fun onStartTrackingTouch(s: SeekBar) {}
                override fun onStopTrackingTouch(s: SeekBar) {}
            })
        }
        pc.addView(pSlider)
        pc.addView(ctx.lbl("BOT IS ALWAYS INCLUDED AS EXTRA.", 10f, C_DIM))
        root.addView(pc)

        // Difficulty
        val dc = ctx.card(C_BORDER_A)
        dc.addView(ctx.lbl("BOT DIFFICULTY", 12f, C_PURPLE, bold = true))
        val dLbl: TextView = ctx.lbl("50  -  MEDIUM", 12f, C_PURPLE, bold = true)
        dc.addView(dLbl)
        val dSlider = SeekBar(ctx).apply {
            max = 99; progress = 49        // 1..100
            layoutParams = ctx.lp(h = 44.dp(ctx), mb = 4)
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar, p: Int, fromUser: Boolean) {
                    val v = p + 1; dLbl.text = "$v  -  ${GameLogic.diffLabel(v)}"
                }
                override fun onStartTrackingTouch(s: SeekBar) {}
                override fun onStopTrackingTouch(s: SeekBar) {}
            })
        }
        dc.addView(dSlider)
        // legend row
        val legRow = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL; layoutParams = ctx.lp(h = 24.dp(ctx))
        }
        listOf("1  EASY" to C_GREEN, "50  MED" to C_ORANGE, "100  EXPERT" to C_RED_B).forEach { (t, c) ->
            legRow.addView(ctx.lbl(t, 10f, c, gravity = android.view.Gravity.CENTER).also {
                (it.layoutParams as LinearLayout.LayoutParams).weight = 1f
            })
        }
        dc.addView(legRow)
        root.addView(dc)
        root.addView(ctx.space(10))

        root.addView(ctx.btnFilled("▶  START GAME", bgColor = C_BTN_FILL, textColor = C_GLOW) {
            val humans = pSlider.progress + 1
            val diff   = dSlider.progress + 1
            AppState.resetGame(humans + 1, humans + 1)
            AppState.gameMode = "bot"
            AppState.botDiff  = diff
            (activity as? MainActivity)?.navigate(GameFragment())
        })
        root.addView(ctx.btnOutline("◀  BACK", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return sv
    }
}
