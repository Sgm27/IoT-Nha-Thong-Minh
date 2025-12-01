package com.example.iot_nha_thong_minh.ui.fire

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.FireAlert
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeEvent
import com.example.iot_nha_thong_minh.ui.chat.GeminiAudioPlayer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class FireUiState(
    val alerts: List<FireAlert> = emptyList(),
    val unacknowledgedCount: Int = 0,
    val isConnected: Boolean = false,
    val statusMessage: String = "Chờ kết nối với hệ thống...",
    val latestAlert: FireAlert? = null,
)

class FireViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(FireUiState())
    val uiState: StateFlow<FireUiState> = _uiState

    private var nextAlertId = 1L
    private val audioPlayer = GeminiAudioPlayer()

    init {
        observeGeminiEvents()
    }

    private fun observeGeminiEvents() {
        viewModelScope.launch {
            repository.geminiEvents.collect { event ->
                when (event) {
                    is GeminiRealtimeEvent.Connected -> {
                        _uiState.update {
                            it.copy(
                                isConnected = true,
                                statusMessage = "Đang giám sát..."
                            )
                        }
                    }
                    is GeminiRealtimeEvent.SetupComplete -> {
                        _uiState.update {
                            it.copy(
                                isConnected = true,
                                statusMessage = "Hệ thống phát hiện cháy đang hoạt động"
                            )
                        }
                    }
                    is GeminiRealtimeEvent.Disconnected -> {
                        _uiState.update {
                            it.copy(
                                isConnected = false,
                                statusMessage = "Mất kết nối, đang thử kết nối lại..."
                            )
                        }
                    }
                    is GeminiRealtimeEvent.FireAlert -> {
                        onFireAlert(event)
                    }
                    else -> { /* ignore other events */ }
                }
            }
        }
    }

    private fun onFireAlert(event: GeminiRealtimeEvent.FireAlert) {
        val alert = FireAlert(
            id = nextAlertId++,
            message = event.message.ifBlank { "Cảnh báo cháy!" },
            confidence = event.detection?.confidence,
            fireRegions = event.detection?.fireRegions,
            firePercentage = event.detection?.firePercentage,
            totalFireArea = event.detection?.totalFireArea,
            triggeredAt = event.triggeredAt,
            timestampMillis = System.currentTimeMillis(),
            isAcknowledged = false,
        )

        _uiState.update { state ->
            val updatedAlerts = listOf(alert) + state.alerts
            state.copy(
                alerts = updatedAlerts.take(100), // Keep last 100 alerts
                unacknowledgedCount = updatedAlerts.count { !it.isAcknowledged },
                latestAlert = alert,
            )
        }

        // Play audio alert if available
        event.audio?.let { audio ->
            audioPlayer.enqueue(audio)
        }
    }

    fun acknowledgeAlert(alertId: Long) {
        _uiState.update { state ->
            val updatedAlerts = state.alerts.map { alert ->
                if (alert.id == alertId) alert.copy(isAcknowledged = true) else alert
            }
            state.copy(
                alerts = updatedAlerts,
                unacknowledgedCount = updatedAlerts.count { !it.isAcknowledged },
                latestAlert = if (state.latestAlert?.id == alertId) null else state.latestAlert,
            )
        }
    }

    fun acknowledgeAllAlerts() {
        _uiState.update { state ->
            state.copy(
                alerts = state.alerts.map { it.copy(isAcknowledged = true) },
                unacknowledgedCount = 0,
                latestAlert = null,
            )
        }
    }

    fun clearHistory() {
        _uiState.update { state ->
            state.copy(
                alerts = emptyList(),
                unacknowledgedCount = 0,
                latestAlert = null,
            )
        }
    }

    fun dismissLatestAlert() {
        _uiState.update { state ->
            if (state.latestAlert != null) {
                val updatedAlerts = state.alerts.map { alert ->
                    if (alert.id == state.latestAlert.id) alert.copy(isAcknowledged = true) else alert
                }
                state.copy(
                    alerts = updatedAlerts,
                    unacknowledgedCount = updatedAlerts.count { !it.isAcknowledged },
                    latestAlert = null,
                )
            } else {
                state
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        audioPlayer.release()
    }
}
