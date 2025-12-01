package com.example.iot_nha_thong_minh.ui.motor

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.Motor
import com.example.iot_nha_thong_minh.data.model.MotorAction
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeEvent
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MotorUiState(
    val motors: Map<String, Motor> = emptyMap(),
    val statusMessage: String = "Chờ kết nối với hệ thống...",
    val isConnected: Boolean = false,
)

class MotorViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(MotorUiState())
    val uiState: StateFlow<MotorUiState> = _uiState

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
                                statusMessage = "Đã kết nối với hệ thống"
                            )
                        }
                    }
                    is GeminiRealtimeEvent.SetupComplete -> {
                        _uiState.update {
                            it.copy(
                                isConnected = true,
                                statusMessage = "Sẵn sàng điều khiển động cơ"
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
                    is GeminiRealtimeEvent.MotorControl -> {
                        onMotorUpdate(event.name, event.action, event.speed)
                    }
                    else -> { /* ignore other events */ }
                }
            }
        }
    }

    private fun onMotorUpdate(name: String, action: String, speed: Float) {
        val motor = Motor(
            name = name,
            action = MotorAction.fromString(action),
            speed = speed,
            updatedAtMillis = System.currentTimeMillis(),
        )
        _uiState.update { state ->
            val updatedMotors = state.motors.toMutableMap()
            updatedMotors[name] = motor
            state.copy(motors = updatedMotors)
        }
    }

    fun sendMotorCommand(motorName: String, action: MotorAction, speed: Float = 1.0f) {
        val command = buildMotorCommand(motorName, action, speed)
        val sent = repository.sendGeminiText(command)
        if (!sent) {
            _uiState.update {
                it.copy(statusMessage = "Không thể gửi lệnh điều khiển. Kiểm tra kết nối.")
            }
        }
    }

    private fun buildMotorCommand(motorName: String, action: MotorAction, speed: Float): String {
        val actionText = when (action) {
            MotorAction.ON -> "bật"
            MotorAction.OFF -> "tắt"
            MotorAction.FORWARD -> "quay thuận"
            MotorAction.BACKWARD -> "quay nghịch"
            MotorAction.STOP -> "dừng"
        }
        val speedPercent = (speed * 100).toInt()
        return if (action == MotorAction.ON || action == MotorAction.FORWARD || action == MotorAction.BACKWARD) {
            "$actionText $motorName với tốc độ $speedPercent%"
        } else {
            "$actionText $motorName"
        }
    }
}
