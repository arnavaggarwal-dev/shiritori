package com.shiritori.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SeekBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.GameClient
import com.shiritori.GameServer
import com.shiritori.MainActivity
import com.shiritori.R

class HostSetupFragment : Fragment() {

    private var errLbl: TextView? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("HOST GAME", 20f, C_ACCENT))
        root.addView(ctx.space(16))

        val card = ctx.card()
        card.addView(ctx.lbl("NUMBER OF PLAYERS", 12f, C_DIM))
        val countLbl: TextView = ctx.lbl("2 PLAYERS", 13f, C_GLOW, bold = true)
        card.addView(countLbl)
        val slider = SeekBar(ctx).apply {
            max = 6; progress = 0
            layoutParams = ctx.lp(h = 44.dp(ctx), mb = 4)
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar, p: Int, fromUser: Boolean) { countLbl.text = "${p+2} PLAYERS" }
                override fun onStartTrackingTouch(s: SeekBar) {}
                override fun onStopTrackingTouch(s: SeekBar) {}
            })
        }
        card.addView(slider)
        root.addView(card)

        errLbl = ctx.lbl("", 11f, C_RED_B)
        root.addView(errLbl!!)
        root.addView(ctx.space(10))

        root.addView(ctx.btnFilled("▶  CREATE LOBBY") { createLobby(slider.progress + 2) })
        root.addView(ctx.btnOutline("◀  BACK", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return sv
    }

    private fun createLobby(n: Int) {
        val act = activity ?: return
        AppState.gameMode = "network"; AppState.nPlayers = n; AppState.botNum = null

        // Create server — on_event routes player_joined to WaitingFragment via the UI thread
        AppState.server = GameServer(n) { msg ->
            act.runOnUiThread {
                if (msg.optString("type") == "player_joined") {
                    (act as? MainActivity)
                        ?.supportFragmentManager?.findFragmentById(R.id.container)
                        ?.let { frag -> if (frag is WaitingFragment) frag.updateCount(msg.optInt("count"), n) }
                }
            }
        }

        // Client messages are routed via AppState (WaitingFragment or NetGameFragment handles them)
        AppState.client = GameClient(
            onMessage    = { msg -> AppState.deliverNetMsg(msg) },
            onDisconnect = { AppState.deliverNetDisconnect() }
        )

        // Navigate to waiting room (it will route messages until game_start)
        (activity as? MainActivity)?.navigate(WaitingFragment())

        // Start server and self-connect in background
        Thread({ startServer() }, "shiritori-host-setup").start()
    }

    private fun startServer() {
        try {
            AppState.server!!.listen()
            Thread.sleep(400)                           // give accept loop time to start
            AppState.client!!.connect("127.0.0.1")     // host joins as player 1
        } catch (e: Exception) {
            activity?.runOnUiThread { errLbl?.text = "ERROR: ${e.message}" }
            AppState.netCleanup()
        }
    }

    override fun onDestroyView() { super.onDestroyView(); errLbl = null }
}
