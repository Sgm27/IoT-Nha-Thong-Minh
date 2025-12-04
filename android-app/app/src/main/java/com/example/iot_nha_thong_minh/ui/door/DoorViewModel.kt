package com.example.iot_nha_thong_minh.ui.door

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.Door
import com.example.iot_nha_thong_minh.data.model.toDomain
import com.example.iot_nha_thong_minh.data.model.toDoorUpdates
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.retryWhen
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DoorsUiState(
    val isLoading: Boolean = false,
    val doors: List<Door> = emptyList(),
    val errorMessage: String? = null,
)

class DoorViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(DoorsUiState(isLoading = true))
    val uiState: StateFlow<DoorsUiState> = _uiState

    init {
        refreshDoors()
        observeDoorStream()
    }

    private fun refreshDoors() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            try {
                val doors = repository.fetchDoors().map { it.toDomain() }
                _uiState.update { state ->
                    state.copy(isLoading = false, doors = doors)
                }
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Không thể tải danh sách cửa",
                    )
                }
            }
        }
    }

    private fun observeDoorStream() {
        viewModelScope.launch {
            repository.observeDoors()
                .retryWhen { _, _ ->
                    delay(3000)
                    true
                }
                .collect { message ->
                    val updates = message.toDoorUpdates()
                    if (updates.isEmpty()) return@collect
                    _uiState.update { state ->
                        val current = state.doors.associateBy { it.location.lowercase() }.toMutableMap()
                        updates.forEach { door ->
                            current[door.location.lowercase()] = door
                        }
                        state.copy(doors = current.values.sortedBy { it.location })
                    }
                }
        }
    }

    fun openDoor(door: Door) {
        viewModelScope.launch {
            try {
                repository.openDoor(door.location)
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể mở cửa")
                }
            }
        }
    }

    fun closeDoor(door: Door) {
        viewModelScope.launch {
            try {
                repository.closeDoor(door.location)
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể đóng cửa")
                }
            }
        }
    }
}
