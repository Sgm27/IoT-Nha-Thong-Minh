package com.example.iot_nha_thong_minh

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.DoorFront
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.LocalFireDepartment
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
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
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.iot_nha_thong_minh.ui.theme.IoTNhaThongMinhTheme
import com.example.iot_nha_thong_minh.data.NetworkModule
import com.example.iot_nha_thong_minh.ui.AppViewModelFactory
import com.example.iot_nha_thong_minh.ui.chat.ChatScreen
import com.example.iot_nha_thong_minh.ui.chat.ChatViewModel
import com.example.iot_nha_thong_minh.ui.door.DoorScreen
import com.example.iot_nha_thong_minh.ui.door.DoorViewModel
import com.example.iot_nha_thong_minh.ui.fire.FireScreen
import com.example.iot_nha_thong_minh.ui.fire.FireViewModel
import com.example.iot_nha_thong_minh.ui.lights.LightsScreen
import com.example.iot_nha_thong_minh.ui.lights.LightsViewModel
import com.example.iot_nha_thong_minh.ui.motor.MotorScreen
import com.example.iot_nha_thong_minh.ui.motor.MotorViewModel
import com.example.iot_nha_thong_minh.ui.music.MusicScreen
import com.example.iot_nha_thong_minh.ui.music.MusicViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Initialize database before accessing repository
        NetworkModule.initialize(applicationContext)
        enableEdgeToEdge()
        setContent {
            IoTNhaThongMinhTheme {
                SmartHomeApp()
            }
        }
    }
}

private enum class HomeTab(val label: String, val icon: ImageVector) {
    CHAT("Trợ lý", Icons.Default.Mic),
    LIGHTS("Đèn", Icons.Default.Lightbulb),
    DOOR("Cửa", Icons.Default.DoorFront),
    MOTOR("Quạt", Icons.Default.Air),
    FIRE("Cháy", Icons.Default.LocalFireDepartment),
    MUSIC("Nhạc", Icons.Default.MusicNote),
}

@Composable
private fun SmartHomeApp() {
    val factory = remember { AppViewModelFactory(NetworkModule.repository) }
    val chatViewModel: ChatViewModel = viewModel(factory = factory)
    val lightsViewModel: LightsViewModel = viewModel(factory = factory)
    val doorViewModel: DoorViewModel = viewModel(factory = factory)
    val musicViewModel: MusicViewModel = viewModel(factory = factory)
    val motorViewModel: MotorViewModel = viewModel(factory = factory)
    val fireViewModel: FireViewModel = viewModel(factory = factory)

    var selectedTab by rememberSaveable { mutableStateOf(HomeTab.CHAT) }

    // Get fire alert count for badge
    val fireUiState by fireViewModel.uiState.collectAsStateWithLifecycle()
    val unacknowledgedCount = fireUiState.unacknowledgedCount

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar {
                HomeTab.entries.forEach { tab ->
                    NavigationBarItem(
                        selected = tab == selectedTab,
                        onClick = { selectedTab = tab },
                        icon = {
                            if (tab == HomeTab.FIRE && unacknowledgedCount > 0) {
                                BadgedBox(
                                    badge = {
                                        Badge { Text(unacknowledgedCount.toString()) }
                                    }
                                ) {
                                    Icon(tab.icon, contentDescription = tab.label)
                                }
                            } else {
                                Icon(tab.icon, contentDescription = tab.label)
                            }
                        },
                        label = { Text(tab.label) },
                    )
                }
            }
        },
    ) { innerPadding ->
        when (selectedTab) {
            HomeTab.CHAT -> ChatScreen(viewModel = chatViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.LIGHTS -> LightsScreen(viewModel = lightsViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.DOOR -> DoorScreen(viewModel = doorViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.MOTOR -> MotorScreen(viewModel = motorViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.FIRE -> FireScreen(viewModel = fireViewModel, modifier = Modifier.padding(innerPadding))
            HomeTab.MUSIC -> MusicScreen(viewModel = musicViewModel, modifier = Modifier.padding(innerPadding))
        }
    }
}