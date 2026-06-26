package com.shiritori

import android.os.Handler
import android.os.Looper
import org.json.JSONArray
import org.json.JSONObject
import java.net.InetSocketAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.Random
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

const val PORT = 55731

// ── Low-level framing ─────────────────────────────────────────────────────────

private fun sendMsg(socket: Socket, obj: JSONObject) {
    val data = obj.toString().toByteArray(Charsets.UTF_8)
    val out  = socket.getOutputStream()
    val hdr  = ByteArray(4).also {
        it[0] = (data.size shr 24).toByte(); it[1] = (data.size shr 16).toByte()
        it[2] = (data.size shr 8).toByte();  it[3] = data.size.toByte()
    }
    synchronized(out) { out.write(hdr); out.write(data); out.flush() }
}

private fun recvMsg(socket: Socket): JSONObject? {
    return try {
        val inp  = socket.getInputStream()
        val hdr  = ByteArray(4); var r = 0
        while (r < 4) { val n = inp.read(hdr, r, 4 - r); if (n < 0) return null; r += n }
        val len  = ((hdr[0].toInt() and 0xFF) shl 24) or ((hdr[1].toInt() and 0xFF) shl 16) or
                   ((hdr[2].toInt() and 0xFF) shl 8)  or  (hdr[3].toInt() and 0xFF)
        val data = ByteArray(len); r = 0
        while (r < len) { val n = inp.read(data, r, len - r); if (n < 0) return null; r += n }
        JSONObject(String(data, Charsets.UTF_8))
    } catch (e: Exception) { null }
}

fun getLocalIp(): String = try {
    Socket().use { s -> s.connect(InetSocketAddress("8.8.8.8", 80)); s.localAddress.hostAddress ?: "127.0.0.1" }
} catch (e: Exception) { "127.0.0.1" }

// ── Game Server ───────────────────────────────────────────────────────────────

class GameServer(val numPlayers: Int, val onEvent: (JSONObject) -> Unit) {

    private val clients       = ConcurrentHashMap<Int, Socket>()
    private val lock          = ReentrantLock()
    private val scores        = IntArray(numPlayers)
    private val activePlayers = mutableListOf<Int>().also { it.addAll(1..numPlayers) }
    private val wordlist      = mutableListOf("apple")
    private var forbidden     = ('a' + Random().nextInt(26)).toChar()
    private var currentPlayer = 1
    private var previousWord  = "apple"
    @Volatile private var timerGen = 0
    private lateinit var serverSocket: ServerSocket

    fun listen() {
        serverSocket = ServerSocket().apply { reuseAddress = true; bind(java.net.InetSocketAddress(PORT)) }
        thread(isDaemon = true, name = "shiritori-accept") { acceptLoop() }
    }

    private fun acceptLoop() {
        var count = 0
        while (count < numPlayers) {
            val conn = try { serverSocket.accept() } catch (e: Exception) { return }
            count++; val pnum = count
            lock.withLock { clients[pnum] = conn }
            sendMsg(conn, JSONObject().apply { put("type","welcome"); put("player_num",pnum); put("num_players",numPlayers) })
            onEvent(JSONObject().apply { put("type","player_joined"); put("count",count) })
            thread(isDaemon = true, name = "shiritori-client-$pnum") { clientLoop(pnum, conn) }
        }
        broadcast(state().put("type","game_start"))
        startTimer()
    }

    private fun clientLoop(pnum: Int, conn: Socket) {
        while (true) {
            val msg = recvMsg(conn) ?: break
            if (msg.optString("type") == "action") lock.withLock { handleAction(pnum, msg.getString("word")) }
        }
        lock.withLock { handleDisconnect(pnum) }
    }

    private fun handleDisconnect(pnum: Int) {
        if (pnum !in activePlayers) return
        val nextP = if (currentPlayer == pnum) next() else currentPlayer
        activePlayers.remove(pnum); clients.remove(pnum)
        val note = "P$pnum DISCONNECTED."
        when {
            activePlayers.size == 1 -> { stopTimer(); broadcast(state().put("type","game_end").put("winner",activePlayers[0]).put("msg",note)) }
            activePlayers.isEmpty() -> stopTimer()
            else -> {
                if (currentPlayer == pnum) currentPlayer = nextP
                broadcast(state().put("type","state_update").put("msg",note).put("color","orange"))
                startTimer()
            }
        }
    }

    private fun handleAction(pnum: Int, word: String) {
        if (pnum != currentPlayer) return
        when { word == "/skip" -> doSkip(pnum); word.startsWith("/donate") -> doDonate(pnum, word); else -> processWord(pnum, word) }
    }

    private fun processWord(pnum: Int, word: String) {
        when {
            word in wordlist -> { sendTo(pnum, msg("ALREADY USED.", "red")); return }
            GameLogic.dictionarySet.isNotEmpty() && word !in GameLogic.dictionarySet -> { sendTo(pnum, msg("\"${word.uppercase()}\" NOT A WORD.", "red")); return }
            word[0] != previousWord.last() -> { sendTo(pnum, msg("MUST START WITH \"${previousWord.last().uppercaseChar()}\".", "red")); return }
            word.last() == forbidden -> {
                val nextP = next(); activePlayers.remove(pnum)
                val m = "P$pnum OUT! ENDED WITH '${forbidden.uppercaseChar()}'."
                if (activePlayers.size == 1) { stopTimer(); broadcast(state().put("type","game_end").put("winner",activePlayers[0]).put("msg",m)) }
                else { currentPlayer = nextP; broadcast(state().put("type","state_update").put("msg",m).put("color","red")); startTimer() }
                return
            }
        }
        wordlist.add(word); scores[pnum - 1] += word.length; previousWord = word; currentPlayer = next()
        broadcast(state().put("type","state_update").put("msg","P$pnum: '${word.uppercase()}' +${word.length}").put("color","green"))
        startTimer()
    }

    private fun doSkip(pnum: Int) {
        val o = Random().nextInt(3)
        if (o == 2) {
            val nextP = next(); activePlayers.remove(pnum)
            val m = "P$pnum ELIMINATED!"
            if (activePlayers.size == 1) { stopTimer(); broadcast(state().put("type","game_end").put("winner",activePlayers[0]).put("msg",m)); return }
            currentPlayer = nextP; broadcast(state().put("type","state_update").put("msg",m).put("color","red")); startTimer(); return
        }
        val (m, col) = if (o == 0) { scores[pnum - 1] = maxOf(0, scores[pnum - 1] - 10); "P$pnum SKIPPED. -10." to "orange" }
                        else "P$pnum SKIPPED SAFELY." to "green"
        currentPlayer = next()
        broadcast(state().put("type","state_update").put("msg",m).put("color",col))
        startTimer()
    }

    private fun doDonate(pnum: Int, raw: String) {
        val parts = raw.split(" ")
        if (parts.size != 3) { sendTo(pnum, msg("/DONATE <PTS> <P>", "red")); return }
        val amt    = parts[1].toIntOrNull() ?: run { sendTo(pnum, msg("INVALID.", "red")); return }
        val target = parts[2].toIntOrNull() ?: run { sendTo(pnum, msg("INVALID.", "red")); return }
        if (amt <= 0 || target < 1 || target > numPlayers || target == pnum || target !in activePlayers) { sendTo(pnum, msg("INVALID.", "red")); return }
        val actual = minOf(amt, scores[pnum - 1]); scores[pnum - 1] -= actual; scores[target - 1] += actual
        currentPlayer = next()
        broadcast(state().put("type","state_update").put("msg","P$pnum DONATED $actual TO P$target.").put("color","accent"))
        startTimer()
    }

    private fun next(): Int {
        val idx = activePlayers.indexOf(currentPlayer)
        return activePlayers[(idx + 1) % activePlayers.size]
    }

    private fun startTimer() {
        timerGen++; val gen = timerGen; var t = 30
        thread(isDaemon = true, name = "shiritori-timer") {
            while (true) {
                if (timerGen != gen) return@thread
                broadcast(JSONObject().apply { put("type","tick"); put("time_left",t) })
                if (t == 0) { if (timerGen == gen) { timerGen++; lock.withLock { doSkip(currentPlayer) } }; return@thread }
                Thread.sleep(1000); t--
            }
        }
    }

    private fun stopTimer() { timerGen++ }

    private fun state(): JSONObject {
        val sc  = JSONArray(); scores.forEach { sc.put(it) }
        val act = JSONArray(); activePlayers.forEach { act.put(it) }
        val wl  = JSONArray(); wordlist.forEach { wl.put(it) }
        return JSONObject().apply {
            put("current_player", currentPlayer); put("previous_word", previousWord)
            put("wordlist", wl); put("scores", sc)
            put("active_players", act); put("forbidden", forbidden.toString())
            put("num_players", numPlayers)
        }
    }

    private fun broadcast(m: JSONObject) { clients.values.forEach { try { sendMsg(it, m) } catch (e: Exception) {} } }
    private fun sendTo(pnum: Int, m: JSONObject) { clients[pnum]?.let { try { sendMsg(it, m) } catch (e: Exception) {} } }
    private fun msg(text: String, color: String) = JSONObject().apply { put("type","msg"); put("text",text); put("color",color) }

    fun shutdown() {
        stopTimer()
        clients.values.forEach { try { it.close() } catch (_: Exception) {} }; clients.clear()
        try { serverSocket.close() } catch (_: Exception) {}
    }
}

// ── Game Client ───────────────────────────────────────────────────────────────

class GameClient(val onMessage: (JSONObject) -> Unit, val onDisconnect: (() -> Unit)? = null) {

    private var socket: Socket? = null
    private val uiHandler = Handler(Looper.getMainLooper())

    fun connect(host: String) {
        val s = Socket(); s.soTimeout = 10_000; s.connect(InetSocketAddress(host, PORT)); s.soTimeout = 0
        socket = s
        thread(isDaemon = true, name = "shiritori-recv") { recvLoop(s) }
    }

    fun sendAction(word: String) {
        val s = socket ?: return
        thread(isDaemon = true) { try { sendMsg(s, JSONObject().apply { put("type","action"); put("word",word) }) } catch (_: Exception) {} }
    }

    private fun recvLoop(s: Socket) {
        while (true) {
            val msg = recvMsg(s) ?: break
            val m   = msg; uiHandler.post { onMessage(m) }
        }
        uiHandler.post { onDisconnect?.invoke() }
    }

    fun disconnect() { try { socket?.close() } catch (_: Exception) {} }
}

