package com.shiritori

object AppState {
    // Game mode: "local" | "bot" | "network"
    var gameMode: String = "local"

    // Players
    var nPlayers: Int = 2
    var botNum: Int? = null
    var botDiff: Int = 50

    // Per-round state
    var scores: MutableList<Int> = mutableListOf()
    var active: MutableList<Int> = mutableListOf()
    var wordlist: MutableList<String> = mutableListOf()
    var wset: MutableSet<String> = mutableSetOf()
    var forbidden: Char = 'x'
    var current: Int = 1
    var prevword: String = "apple"
    var notepad: MutableList<String> = mutableListOf()
    var timeLeft: Int = 30

    // End state
    var winner: Int = 1
    var playerNum: Int? = null
    var endMsg: String = ""

    // Networking
    var server: GameServer? = null
    var client: GameClient? = null

    // Net-game state cache (populated from server messages)
    var netEndScores: List<Int> = emptyList()
    var netActive: List<Int> = emptyList()
    var netNPlayers: Int = 0
    var netWordlist: List<String> = emptyList()

    // Message routing for net game screen
    var netMsgHandler: ((org.json.JSONObject) -> Unit)? = null
    var netDisconnectHandler: (() -> Unit)? = null
    val pendingNetMsgs: ArrayDeque<org.json.JSONObject> = ArrayDeque()

    fun deliverNetMsg(msg: org.json.JSONObject) {
        val h = netMsgHandler
        if (h != null) h(msg) else pendingNetMsgs.addLast(msg)
    }

    fun deliverNetDisconnect() {
        netDisconnectHandler?.invoke()
    }

    fun netCleanup() {
        server?.shutdown(); server = null
        client?.disconnect(); client = null
        netMsgHandler = null
        netDisconnectHandler = null
        pendingNetMsgs.clear()
    }

    fun resetGame(n: Int, bot: Int?) {
        nPlayers = n; botNum = bot
        scores = MutableList(n) { 0 }
        active = MutableList(n) { it + 1 }
        wordlist = mutableListOf("apple")
        wset = mutableSetOf("apple")
        forbidden = ('a' + (0..25).random()).toChar()
        current = 1; prevword = "apple"
        notepad = mutableListOf()
        timeLeft = 30
        playerNum = null
    }
}
