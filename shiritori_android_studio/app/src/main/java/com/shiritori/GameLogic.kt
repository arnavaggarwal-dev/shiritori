package com.shiritori

import android.content.Context
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import kotlin.math.roundToInt

object GameLogic {

    var dictionary: List<String> = emptyList()
        private set
    var dictionarySet: Set<String> = emptySet()
        private set

    private val wordsByLetter = mutableMapOf<Char, MutableList<String>>()

    fun load(context: Context) {
        try {
            val reader = BufferedReader(InputStreamReader(context.assets.open("words_dictionary.json")))
            val sb = StringBuilder(); var line: String?
            while (reader.readLine().also { line = it } != null) sb.append(line)
            val json = JSONObject(sb.toString())
            val keys = mutableListOf<String>()
            val iter = json.keys(); while (iter.hasNext()) keys.add(iter.next())
            dictionary    = keys
            dictionarySet = keys.toSet()
            keys.forEach { w -> wordsByLetter.getOrPut(w[0]) { mutableListOf() }.add(w) }
        } catch (e: Exception) {
            dictionary = emptyList(); dictionarySet = emptySet()
        }
    }

    /**
     * Build pool: difficulty% safe words + (100-difficulty)% forbidden-ending words.
     * Bot picks randomly — caller eliminates if chosen word ends with forbidden.
     * difficulty=100 → 0% danger (hardest); difficulty=0 → 100% danger (easiest).
     */
    fun botPick(start: Char, wset: Set<String>, forbidden: Char, difficulty: Int): String? {
        val cands = wordsByLetter[start]?.filter { it !in wset && it.length > 1 } ?: emptyList()
        if (cands.isEmpty()) return null
        val safe   = cands.filter { it.last() != forbidden }
        val danger = cands.filter { it.last() == forbidden }
        val dangerN = (danger.size * (100 - difficulty) / 100.0).roundToInt()
        val safeN   = (safe.size   * difficulty         / 100.0).roundToInt()
        val pool = danger.shuffled().take(dangerN) + safe.shuffled().take(safeN)
        val chosen = pool.ifEmpty { safe.ifEmpty { danger } }
        if (danger.isNotEmpty() && Math.random() < 0.01) return danger.random()
        return chosen.randomOrNull()
    }

    fun diffLabel(d: Int): String = when {
        d <= 20 -> "EASY"
        d <= 40 -> "MED-EASY"
        d <= 60 -> "MEDIUM"
        d <= 80 -> "HARD"
        else    -> "EXPERT"
    }
}
