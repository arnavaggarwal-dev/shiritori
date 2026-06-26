package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.MainActivity
import com.shiritori.PORT
import com.shiritori.getLocalIp

/**
 * Shows host IP / "Connecting…" while waiting for all players.
 * Also acts as the net-message router: queues messages in AppState.pendingNetMsgs
 * and navigates to NetGameFragment when "game_start" arrives.
 */
class WaitingFragment : Fragment() {

    private var connLbl: TextView? = null
    private var storedCount = 0
    private var navigatingAway = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(40))
        root.addView(ctx.bigLbl("LOBBY", 22f, C_ACCENT))
        root.addView(ctx.lbl("WAITING FOR PLAYERS...", 12f, C_DIM, gravity = android.view.Gravity.CENTER))
        root.addView(ctx.space(16))

        // Show IP only when hosting
        if (AppState.server != null) {
            val ip   = getLocalIp()
            val card = ctx.card()
            card.addView(ctx.lbl("YOUR IP — SHARE WITH PLAYERS", 11f, C_DIM))
            card.addView(ctx.bigLbl(ip, 22f, C_GLOW))
            card.addView(ctx.lbl("PORT: $PORT", 10f, C_DIM))
            root.addView(card)
        }

        root.addView(ctx.space(12))
        val n = AppState.nPlayers
        connLbl = ctx.lbl(
            if (AppState.server != null) "$storedCount / $n CONNECTED" else "CONNECTING...",
            13f, C_ACCENT, bold = true, gravity = android.view.Gravity.CENTER
        )
        root.addView(connLbl!!)
        root.addView(ctx.lbl("GAME STARTS AUTOMATICALLY.", 11f, C_DIM, gravity = android.view.Gravity.CENTER))
        root.addView(ctx.space(20))
        root.addView(ctx.btnOutline("◀  CANCEL", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return sv
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // If disconnected while waiting, go back to lobby
        AppState.netDisconnectHandler = {
            activity?.runOnUiThread { if (isAdded) (activity as? MainActivity)?.navigateToLobby() }
        }

        // Act as the net-message pre-game router
        AppState.netMsgHandler = { msg ->
            activity?.runOnUiThread {
                if (!isAdded || navigatingAway) return@runOnUiThread
                when (msg.optString("type")) {
                    "welcome" -> {
                        val pnum = msg.optInt("player_num")
                        connLbl?.text = "YOU ARE P$pnum — WAITING..."
                    }
                    "player_joined" -> {
                        val cnt = msg.optInt("count")
                        storedCount = cnt
                        val total = AppState.nPlayers
                        connLbl?.text = "$cnt / $total CONNECTED"
                    }
                    "game_start" -> {
                        navigatingAway = true
                        AppState.pendingNetMsgs.addLast(msg)          // NetGameFragment drains this
                        (activity as? MainActivity)?.navigate(NetGameFragment())
                    }
                    else -> AppState.pendingNetMsgs.addLast(msg)       // queue for NetGameFragment
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        if (!navigatingAway) {
            AppState.netMsgHandler       = null
            AppState.netDisconnectHandler= null
        }
        connLbl = null
    }

    fun updateCount(count: Int, total: Int) {
        storedCount = count
        activity?.runOnUiThread { connLbl?.text = "$count / $total CONNECTED" }
    }
}
