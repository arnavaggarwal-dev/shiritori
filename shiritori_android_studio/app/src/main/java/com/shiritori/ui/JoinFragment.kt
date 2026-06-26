package com.shiritori.ui

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Spinner
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.shiritori.AppState
import com.shiritori.GameClient
import com.shiritori.MainActivity

class JoinFragment : Fragment() {

    private var msgLbl: TextView? = null
    private var ipEntry: android.widget.EditText? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val ctx = requireContext()
        val (sv, root) = ctx.scrollRoot()

        root.addView(ctx.space(24))
        root.addView(ctx.bigLbl("JOIN GAME", 20f, C_ACCENT))
        root.addView(ctx.space(16))

        val card = ctx.card()
        card.addView(ctx.lbl("HOST IP ADDRESS", 12f, C_DIM))
        ipEntry = ctx.textIn("192.168.X.XX")
        card.addView(ipEntry!!)

        val history = loadIpHistory(ctx)
        if (history.isNotEmpty()) {
            card.addView(ctx.lbl("RECENT:", 10f, C_DIM))
            val spinner = Spinner(ctx).apply {
                val items = listOf("SELECT RECENT IP...") + history
                adapter = ArrayAdapter(ctx, android.R.layout.simple_spinner_item, items)
                    .also { it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
                layoutParams = ctx.lp(h = 48.dp(ctx), mb = 4)
                onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(p: android.widget.AdapterView<*>, v: View?, pos: Int, id: Long) {
                        if (pos > 0) ipEntry?.setText(history[pos - 1])
                    }
                    override fun onNothingSelected(p: android.widget.AdapterView<*>) {}
                }
            }
            card.addView(spinner)
            card.addView(ctx.btnOutline("CLEAR HISTORY", C_DIM, C_DIM, mb = 0) {
                clearHistory(ctx); (activity as? MainActivity)?.navigate(JoinFragment())
            })
        }
        root.addView(card)

        msgLbl = ctx.lbl("", 11f, C_RED_B)
        root.addView(msgLbl!!)
        root.addView(ctx.space(10))
        root.addView(ctx.btnFilled("▶  CONNECT") { doConnect(ctx) })
        root.addView(ctx.btnOutline("◀  BACK", C_DIM, C_DIM) {
            (activity as? MainActivity)?.navigateToLobby()
        })

        return sv
    }

    private fun doConnect(ctx: Context) {
        val ip = ipEntry?.text?.toString()?.trim() ?: ""
        if (ip.isEmpty()) { msgLbl?.text = "ENTER AN IP."; return }
        msgLbl?.text = "CONNECTING..."
        saveIpToHistory(ctx, ip)

        AppState.gameMode = "network"; AppState.nPlayers = 0  // will be filled by "welcome"

        val act = activity ?: return
        AppState.client = GameClient(
            onMessage    = { msg -> AppState.deliverNetMsg(msg) },
            onDisconnect = { AppState.deliverNetDisconnect() }
        )

        // Navigate to waiting screen (it routes messages until game_start → NetGameFragment)
        (activity as? MainActivity)?.navigate(WaitingFragment())

        Thread({
            try { AppState.client!!.connect(ip) }
            catch (e: Exception) {
                act.runOnUiThread { msgLbl?.text = "FAILED: ${e.message}" }
                AppState.netCleanup()
            }
        }, "shiritori-join").start()
    }

    private fun clearHistory(ctx: Context) {
        ctx.getSharedPreferences("shiritori", Context.MODE_PRIVATE).edit().remove("ip_history").apply()
    }

    override fun onDestroyView() { super.onDestroyView(); msgLbl = null; ipEntry = null }
}

// ── IP history helpers ────────────────────────────────────────────────────────

fun loadIpHistory(ctx: Context): List<String> {
    val raw = ctx.getSharedPreferences("shiritori", Context.MODE_PRIVATE).getString("ip_history", "") ?: ""
    return if (raw.isBlank()) emptyList() else raw.split(",").filter { it.isNotBlank() }
}

fun saveIpToHistory(ctx: Context, ip: String) {
    val h = loadIpHistory(ctx).toMutableList()
    h.remove(ip); h.add(0, ip)
    ctx.getSharedPreferences("shiritori", Context.MODE_PRIVATE)
        .edit().putString("ip_history", h.take(10).joinToString(",")).apply()
}
