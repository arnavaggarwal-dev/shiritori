package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SeekBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.MainActivity

class LocalSetupFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("LOCAL GAME", 20f, C_ACCENT))
        root.addView(ctx.space(16))

        val card = ctx.card()
        card.addView(ctx.lbl("NUMBER OF PLAYERS", 12f, C_DIM))

        val countLbl: TextView = ctx.lbl("2 PLAYERS", 13f, C_GLOW, bold = true)
        card.addView(countLbl)

        val slider = SeekBar(ctx).apply {
            max = 6; progress = 0          // 2..8 → offset by 2
            layoutParams = ctx.lp(h = 44.dp(ctx), mb = 4)
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar, p: Int, fromUser: Boolean) {
                    val n = p + 2; countLbl.text = "$n PLAYERS"
                }
                override fun onStartTrackingTouch(s: SeekBar) {}
                override fun onStopTrackingTouch(s: SeekBar) {}
            })
        }
        card.addView(slider)
        root.addView(card)
        root.addView(ctx.space(10))

        root.addView(ctx.btnFilled("▶  START GAME") {
            val n = slider.progress + 2
            AppState.resetGame(n, null); AppState.gameMode = "local"
            (activity as? MainActivity)?.navigate(GameFragment())
        })
        root.addView(ctx.btnOutline("◀  BACK", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return sv
    }
}
