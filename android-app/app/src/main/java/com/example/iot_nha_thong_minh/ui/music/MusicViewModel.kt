package com.example.iot_nha_thong_minh.ui.music

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.MusicPlaybackState
import com.example.iot_nha_thong_minh.data.model.PlaybackStatus
import com.example.iot_nha_thong_minh.data.model.toDomain
import com.example.iot_nha_thong_minh.data.model.toPlaybackState
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.retryWhen
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class MusicUiState(
    val isLoading: Boolean = false,
    val library: List<String> = emptyList(),
    val playbackState: MusicPlaybackState? = null,
    val playbackPosition: Double = 0.0,
    val currentStreamUrl: String? = null,
    val errorMessage: String? = null,
    val infoMessage: String? = null,
)

class MusicViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(MusicUiState(isLoading = true))
    val uiState: StateFlow<MusicUiState> = _uiState

    private var progressJob: Job? = null

    init {
        refreshLibrary()
        refreshPlaybackState()
        observeMusicStream()
    }

    private fun refreshLibrary() {
        viewModelScope.launch {
            try {
                val library = repository.fetchMusicLibrary().sorted()
                _uiState.update { it.copy(library = library, errorMessage = null) }
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể tải thư viện nhạc")
                }
            }
        }
    }

    private fun refreshPlaybackState() {
        viewModelScope.launch {
            try {
                val state = repository.fetchMusicState().toDomain()
                applyPlaybackState(state)
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(errorMessage = error.message ?: "Không thể tải trạng thái phát nhạc")
                }
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    private fun observeMusicStream() {
        viewModelScope.launch {
            repository.observeMusicUpdates()
                .retryWhen { _, _ ->
                    delay(3000)
                    true
                }
                .collect { message ->
                val state = message.toPlaybackState() ?: return@collect
                applyPlaybackState(state)
                }
        }
    }

    private fun scheduleProgressUpdates(state: MusicPlaybackState?) {
        progressJob?.cancel()
        if (state == null) {
            _uiState.update { it.copy(playbackPosition = 0.0) }
            return
        }

        if (state.status == PlaybackStatus.PLAYING) {
            val startPosition = state.positionSeconds
            val startTime = System.currentTimeMillis()
            progressJob = viewModelScope.launch {
                while (isActive) {
                    val elapsed = (System.currentTimeMillis() - startTime) / 1000.0
                    _uiState.update { current ->
                        current.copy(playbackPosition = startPosition + elapsed)
                    }
                    delay(500)
                }
            }
        } else {
            _uiState.update { it.copy(playbackPosition = state.positionSeconds) }
        }
    }

    private fun applyPlaybackState(state: MusicPlaybackState?, streamUrlOverride: String? = null) {
        _uiState.update { previous ->
            val resolvedUrl = when {
                streamUrlOverride != null -> streamUrlOverride
                state?.matchedSong != null -> repository.buildStreamUrlForSong(state.matchedSong)
                else -> null
            }
            val currentUrl = resolvedUrl ?: previous.currentStreamUrl?.takeIf { state?.matchedSong != null }
            previous.copy(
                playbackState = state,
                playbackPosition = state?.positionSeconds ?: 0.0,
                currentStreamUrl = currentUrl,
                errorMessage = null,
                infoMessage = null,
            )
        }
        scheduleProgressUpdates(state)
    }

    fun playSong(title: String) {
        val trimmed = title.trim()
        if (trimmed.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Vui lòng nhập tên bài hát") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            try {
                val response = repository.requestPlayMusic(trimmed)
                val streamUrl = repository.toAbsoluteUrl(response.streamUrl)
                applyPlaybackState(response.playbackState.toDomain(), streamUrl)
                _uiState.update { it.copy(infoMessage = "Đang phát bài: ${response.selectedSong}") }
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(
                        errorMessage = error.message ?: "Không thể phát bài hát",
                        infoMessage = null,
                    )
                }
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    fun pause() {
        viewModelScope.launch {
            try {
                val state = repository.pauseMusic().toDomain()
                applyPlaybackState(state)
            } catch (error: Exception) {
                _uiState.update { it.copy(errorMessage = error.message ?: "Không thể tạm dừng nhạc") }
            }
        }
    }

    fun resume() {
        viewModelScope.launch {
            try {
                val state = repository.resumeMusic().toDomain()
                applyPlaybackState(state)
            } catch (error: Exception) {
                _uiState.update { it.copy(errorMessage = error.message ?: "Không thể tiếp tục phát nhạc") }
            }
        }
    }

    fun seekTo(positionSeconds: Double) {
        viewModelScope.launch {
            try {
                val state = repository.seekMusic(positionSeconds).toDomain()
                applyPlaybackState(state)
            } catch (error: Exception) {
                _uiState.update { it.copy(errorMessage = error.message ?: "Không thể tua bài hát") }
            }
        }
    }
}
