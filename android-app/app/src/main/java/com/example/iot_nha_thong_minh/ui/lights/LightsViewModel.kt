package com.example.iot_nha_thong_minh.ui.lights

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.Light
import com.example.iot_nha_thong_minh.data.model.toDomain
import com.example.iot_nha_thong_minh.data.model.toLightUpdates
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.retryWhen
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class LightsUiState(
    val isLoading: Boolean = false,
    val lights: List<Light> = emptyList(),
    val errorMessage: String? = null,
)

class LightsViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(LightsUiState(isLoading = true))
    val uiState: StateFlow<LightsUiState> = _uiState

    init {
        refreshLights()
        observeLightStream()
    }

    private fun refreshLights() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            try {
                val lights = repository.fetchLights().map { it.toDomain() }
                _uiState.update { state ->
                    state.copy(isLoading = false, lights = lights)
                }
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Không thể tải danh sách đèn",
                    )
                }
            }
        }
    }

    private fun observeLightStream() {
        viewModelScope.launch {
            repository.observeLights()
                .retryWhen { _, _ ->
                    delay(3000)
                    true
                }
                .collect { message ->
                val updates = message.toLightUpdates()
                if (updates.isEmpty()) return@collect
                _uiState.update { state ->
                    val current = state.lights.associateBy { it.location.lowercase() }.toMutableMap()
                    updates.forEach { light ->
                        current[light.location.lowercase()] = light
                    }
                    state.copy(lights = current.values.sortedBy { it.location })
                }
                }
        }
    }

    fun toggleLight(light: Light) {
        viewModelScope.launch {
            try {
                repository.toggleLight(light.location, !light.isOn)
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể cập nhật trạng thái đèn")
                }
            }
        }
    }

    fun turnOnAllLights() {
        viewModelScope.launch {
            try {
                repository.turnOnAllLights()
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể bật tất cả đèn")
                }
            }
        }
    }

    fun turnOffAllLights() {
        viewModelScope.launch {
            try {
                repository.turnOffAllLights()
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể tắt tất cả đèn")
                }
            }
        }
    }
}
