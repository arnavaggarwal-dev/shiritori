package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import androidx.fragment.app.Fragment
import com.shiritori.GameLogic
import com.shiritori.MainActivity
import com.shiritori.PORT

class LobbyFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("✦  SHIRITORI  ✦", 26f, C_ACCENT))
        root.addView(ctx.lbl("CHAIN WORDS  ·  SURVIVE  ·  DOMINATE", 11f, C_DIM, gravity = android.view.Gravity.CENTER))
        root.addView(ctx.space(20))

        // Local / Bot card
        val lc = ctx.card()
        lc.addView(ctx.lbl("[LOCAL / BOT]", 13f, C_ACCENT, bold = true))
        lc.addView(ctx.lbl("Play on this device.", 11f, C_DIM))
        lc.addView(ctx.space(8))
        lc.addView(ctx.btnFilled("▶  PLAY LOCAL", bgColor = C_BTN_FILL) { go(LocalSetupFragment()) })
        lc.addView(ctx.btnFilled("▶  VS BOT",     bgColor = C_BTN_FILL, textColor = C_GLOW) { go(BotSetupFragment()) })
        root.addView(lc)

        // Network card
        val nc = ctx.card()
        nc.addView(ctx.lbl("[NETWORK]", 13f, C_ACCENT, bold = true))
        nc.addView(ctx.lbl("Same WiFi — each player on own device.", 11f, C_DIM))
        nc.addView(ctx.space(8))
        val row = LinearLayout(ctx).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = ctx.lp(h = 52.dp(ctx))
        }
        val btnHost = ctx.btnFilled("▶  HOST") { go(HostSetupFragment()) }
        (btnHost.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0; marginEnd = 8.dp(ctx) }
        val btnJoin = ctx.btnOutline("▶  JOIN") { go(JoinFragment()) }
        (btnJoin.layoutParams as LinearLayout.LayoutParams).apply { weight = 1f; width = 0 }
        row.addView(btnHost); row.addView(btnJoin)
        nc.addView(row)
        root.addView(nc)

        root.addView(ctx.space(8))
        root.addView(ctx.lbl("PORT: $PORT  |  DICT: ${if (com.shiritori.GameLogic.dictionarySet.isNotEmpty()) "LOADED" else "LOADING..."}", 10f, C_DIM, gravity = android.view.Gravity.CENTER))

        return sv
    }

    private fun go(f: Fragment) { (activity as? MainActivity)?.navigate(f) }
}
