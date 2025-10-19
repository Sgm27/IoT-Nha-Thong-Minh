package com.example.iot_nha_thong_minh

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.iot_nha_thong_minh.ui.theme.IoTNhaThongMinhTheme
import com.example.iot_nha_thong_minh.data.NetworkModule
import com.example.iot_nha_thong_minh.ui.AppViewModelFactory
import com.example.iot_nha_thong_minh.ui.chat.ChatScreen
import com.example.iot_nha_thong_minh.ui.chat.ChatViewModel
import com.example.iot_nha_thong_minh.ui.lights.LightsScreen
import com.example.iot_nha_thong_minh.ui.lights.LightsViewModel
import com.example.iot_nha_thong_minh.ui.music.MusicScreen
import com.example.iot_nha_thong_minh.ui.music.MusicViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            IoTNhaThongMinhTheme {
                SmartHomeApp()
            }
        }
    }
}

private enum class HomeTab(val label: String, val icon: ImageVector) {
    CHAT("Trợ lý AI", Icons.Default.Mic),
    LIGHTS("Điều khiển đèn", Icons.Default.Lightbulb),
    MUSIC("Phát nhạc", Icons.Default.MusicNote),
}

@Composable
private fun SmartHomeApp() {
    val factory = remember { AppViewModelFactory(NetworkModule.repository) }
    val chatViewModel: ChatViewModel = viewModel(factory = factory)
    val lightsViewModel: LightsViewModel = viewModel(factory = factory)
    val musicViewModel: MusicViewModel = viewModel(factory = factory)

    var selectedTab by rememberSaveable { mutableStateOf(HomeTab.CHAT) }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar {
                HomeTab.values().forEach { tab ->
                    NavigationBarItem(
                        selected = tab == selectedTab,
                        onClick = { selectedTab = tab },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) },
                    )
                }
            }
        },
    ) { innerPadding ->
        when (selectedTab) {
            HomeTab.CHAT -> ChatScreen(viewModel = chatViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.LIGHTS -> LightsScreen(viewModel = lightsViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.MUSIC -> MusicScreen(viewModel = musicViewModel, modifier = Modifier.padding(innerPadding))
        }
    }
}