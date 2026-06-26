package com.shiritori

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.shiritori.ui.LobbyFragment

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Load dictionary off the main thread
        Thread { GameLogic.load(applicationContext) }.start()

        if (savedInstanceState == null) {
            navigate(LobbyFragment())
        }
    }

    fun navigate(fragment: Fragment) {
        if (!isFinishing && !isDestroyed) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.container, fragment)
                .commit()
        }
    }

    fun navigateToLobby() {
        AppState.netCleanup()
        navigate(LobbyFragment())
    }
}
