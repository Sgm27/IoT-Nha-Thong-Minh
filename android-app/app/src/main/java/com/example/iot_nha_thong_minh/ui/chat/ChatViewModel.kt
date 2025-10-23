package com.example.iot_nha_thong_minh.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.ChatRole
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeAudio
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeEvent
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeTranscription
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val RECONNECT_DELAY_MS = 3_000L

data class ChatUiState(
    val isListening: Boolean = false,
    val messages: List<ChatMessage> = emptyList(),
    val errorMessage: String? = null,
    val statusMessage: String = "Đang kết nối tới Gemini...",
    val isConnected: Boolean = false,
    val isMicPermissionDenied: Boolean = false,
)

class ChatViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private var nextMessageId = 1L
    private var streamingAssistantMessageId: Long? = null
    private var reconnectJob: Job? = null
    private val audioPlayer = GeminiAudioPlayer()
    private var resumeListeningAfterPlayback = false

    init {
        observeGeminiEvents()
        repository.connectGemini()
    }

    fun startListening() {
        updateListeningState(isListening = true)
    }

    fun stopListening() {
        updateListeningState(isListening = false)
    }

    fun onListeningToggleRequested(enabled: Boolean) {
        if (enabled) {
            startListening()
        } else {
            stopListening()
        }
    }

    private fun updateListeningState(isListening: Boolean, clearResumeFlag: Boolean = true) {
        if (clearResumeFlag) {
            resumeListeningAfterPlayback = false
        }
        _uiState.update { state ->
            if (state.isListening == isListening) {
                state
            } else {
                state.copy(isListening = isListening, errorMessage = null)
            }
        }
    }

    fun onMicrophonePermissionGranted() {
        _uiState.update { it.copy(isMicPermissionDenied = false, errorMessage = null) }
    }

    fun onMicrophonePermissionDenied() {
        _uiState.update {
            it.copy(
                isListening = false,
                isMicPermissionDenied = true,
                errorMessage = "Ứng dụng cần quyền micro để trò chuyện bằng giọng nói.",
            )
        }
        resumeListeningAfterPlayback = false
    }

    fun onSpeechError(message: String) {
        _uiState.update { it.copy(errorMessage = message, isListening = false) }
        resumeListeningAfterPlayback = false
    }

    fun sendAudioChunk(data: ByteArray, sampleRate: Int) {
        if (data.isEmpty()) {
            return
        }
        val normalizedRate = if (sampleRate > 0) sampleRate else 16_000
        viewModelScope.launch(Dispatchers.IO) {
            val success = repository.sendGeminiRealtimeAudio(data, normalizedRate)
            if (!success) {
                _uiState.update {
                    it.copy(
                        isListening = false,
                        errorMessage = "Không thể gửi dữ liệu giọng nói tới Gemini. Đang thử kết nối lại...",
                    )
                }
                resumeListeningAfterPlayback = false
                scheduleReconnect()
            }
        }
    }

    fun sendMessage(content: String) {
        val trimmed = content.trim()
        if (trimmed.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Vui lòng nhập nội dung trước khi gửi") }
            return
        }

        val userMessage = ChatMessage(
            id = nextMessageId++,
            role = ChatRole.USER,
            content = trimmed,
            timestampMillis = System.currentTimeMillis(),
            isStreaming = false,
        )

        _uiState.update { state ->
            state.copy(
                messages = state.messages + userMessage,
                errorMessage = null,
            )
        }

        val sent = repository.sendGeminiText(trimmed)
        if (!sent) {
            _uiState.update {
                it.copy(
                    errorMessage = "Không thể gửi tin nhắn tới Gemini. Đang thử kết nối lại...",
                )
            }
            scheduleReconnect()
        }
    }

    override fun onCleared() {
        super.onCleared()
        repository.disconnectGemini()
        audioPlayer.release()
    }

    private fun observeGeminiEvents() {
        viewModelScope.launch {
            repository.geminiEvents.collect { event ->
                when (event) {
                    is GeminiRealtimeEvent.Connected -> onConnected(event)
                    is GeminiRealtimeEvent.SetupComplete -> onSetupComplete(event)
                    is GeminiRealtimeEvent.Disconnected -> onDisconnected(event)
                    is GeminiRealtimeEvent.ConnectionError -> onConnectionError(event)
                    is GeminiRealtimeEvent.Text -> onAssistantText(event.text, finished = true)
                    is GeminiRealtimeEvent.Transcription -> onTranscription(event.transcription)
                    is GeminiRealtimeEvent.Audio -> onAssistantAudio(event.payload)
                    is GeminiRealtimeEvent.ToolCall -> appendSystemMessage(
                        message = event.functionName?.let { "Gemini đang gọi chức năng \"$it\"." }
                            ?: "Gemini đang xử lý một yêu cầu hệ thống.",
                    )
                    is GeminiRealtimeEvent.ScreenNavigation -> appendSystemMessage(
                        message = event.action?.let { "Ứng dụng đang chuyển tới màn hình: $it" }
                            ?: "Ứng dụng đang thực hiện một thao tác điều hướng.",
                    )
                    is GeminiRealtimeEvent.MemoryUpdate -> appendSystemMessage(
                        "Gemini đã ghi nhớ thêm thông tin về bạn để phục vụ tốt hơn trong lần sau.",
                    )
                    is GeminiRealtimeEvent.SmartHomeLightUpdate -> onLightUpdate(event.location, event.isOn)
                    is GeminiRealtimeEvent.SmartHomeMusic -> onMusicUpdate(event.requestedTitle, event.matchedSong)
                    is GeminiRealtimeEvent.SmartHomeMusicControl -> onMusicControl(event)
                }
            }
        }
    }

    private fun onConnected(event: GeminiRealtimeEvent.Connected) {
        reconnectJob?.cancel()
        _uiState.update {
            it.copy(
                isConnected = true,
                statusMessage = event.message ?: "Đã kết nối với Gemini. Bạn có thể trò chuyện ngay!",
                errorMessage = null,
            )
        }
    }

    private fun onSetupComplete(event: GeminiRealtimeEvent.SetupComplete) {
        _uiState.update {
            it.copy(
                isConnected = true,
                statusMessage = event.message ?: "Đã kết nối với Gemini. Bạn có thể trò chuyện ngay!",
            )
        }
    }

    private fun onDisconnected(event: GeminiRealtimeEvent.Disconnected) {
        _uiState.update {
            it.copy(
                isConnected = false,
                statusMessage = event.reason?.takeIf { reason -> reason.isNotBlank() }
                    ?: "Đã ngắt kết nối với Gemini. Đang thử kết nối lại...",
                isListening = false,
            )
        }
        resumeListeningAfterPlayback = false
        scheduleReconnect()
    }

    private fun onConnectionError(event: GeminiRealtimeEvent.ConnectionError) {
        appendSystemMessage(event.message)
        _uiState.update {
            it.copy(
                isConnected = false,
                statusMessage = event.message,
                isListening = false,
            )
        }
        resumeListeningAfterPlayback = false
        scheduleReconnect()
    }

    private fun onAssistantText(text: String, finished: Boolean) {
        if (text.isBlank()) {
            if (finished) {
                streamingAssistantMessageId = null
            }
            return
        }

        val messageId = streamingAssistantMessageId ?: nextMessageId++
        val timestamp = System.currentTimeMillis()
        val appendText = text

        _uiState.update { state ->
            val existing = state.messages.find { it.id == messageId }
            val updatedMessages = if (existing == null) {
                streamingAssistantMessageId = if (finished) null else messageId
                state.messages + ChatMessage(
                    id = messageId,
                    role = ChatRole.ASSISTANT,
                    content = appendText,
                    timestampMillis = timestamp,
                    isStreaming = !finished,
                )
            } else {
                val mergedContent = if (!finished && appendText.startsWith(existing.content)) {
                    appendText
                } else if (finished) {
                    appendText
                } else {
                    existing.content + appendText
                }
                streamingAssistantMessageId = if (finished) null else messageId
                state.messages.map { message ->
                    if (message.id == messageId) {
                        message.copy(
                            content = mergedContent,
                            isStreaming = !finished,
                            timestampMillis = if (finished) timestamp else message.timestampMillis,
                        )
                    } else {
                        message
                    }
                }
            }

            state.copy(messages = updatedMessages)
        }

        if (finished) {
            onAssistantSpeechFinished()
        }
    }

    private fun onTranscription(transcription: GeminiRealtimeTranscription) {
        if (transcription.sender.equals("Gemini", ignoreCase = true)) {
            onAssistantText(transcription.text, transcription.finished)
        }
    }

    private fun onAssistantAudio(audio: GeminiRealtimeAudio) {
        val wasListening = uiState.value.isListening
        if (wasListening) {
            resumeListeningAfterPlayback = true
            updateListeningState(isListening = false, clearResumeFlag = false)
        }
        audioPlayer.enqueue(audio)
    }

    private fun onAssistantSpeechFinished() {
        if (resumeListeningAfterPlayback && uiState.value.isConnected && !uiState.value.isMicPermissionDenied) {
            updateListeningState(isListening = true)
        } else {
            resumeListeningAfterPlayback = false
        }
    }

    private fun onLightUpdate(location: String, isOn: Boolean) {
        if (location.isBlank()) {
            return
        }
        val status = if (isOn) "bật" else "tắt"
        appendSystemMessage("Đèn tại \"$location\" hiện đang $status.")
    }

    private fun onMusicUpdate(requestedTitle: String?, matchedSong: String?) {
        val message = when {
            !matchedSong.isNullOrBlank() -> "Gemini đang phát bài \"$matchedSong\" theo yêu cầu ${requestedTitle ?: ""}."
            !requestedTitle.isNullOrBlank() -> "Không tìm thấy bài hát phù hợp với yêu cầu \"$requestedTitle\"."
            else -> "Gemini đang xử lý yêu cầu phát nhạc của bạn."
        }
        appendSystemMessage(message)
    }

    private fun onMusicControl(event: GeminiRealtimeEvent.SmartHomeMusicControl) {
        val action = event.action.orEmpty()
        val matched = event.matchedSong.orEmpty()
        val message = when (action) {
            "pause" ->
                if (event.status == "paused") {
                    if (matched.isNotBlank()) "Đã tạm dừng bài hát \"$matched\"." else "Đã tạm dừng phát nhạc."
                } else {
                    "Không có bài hát nào đang phát để tạm dừng."
                }
            "continue" ->
                if (event.status == "playing") {
                    if (matched.isNotBlank()) "Tiếp tục phát bài hát \"$matched\"." else "Tiếp tục phát nhạc."
                } else {
                    "Không có bài hát nào đang tạm dừng để tiếp tục."
                }
            else -> null
        }
        if (!message.isNullOrBlank()) {
            appendSystemMessage(message)
        }
    }

    private fun appendSystemMessage(message: String) {
        val trimmed = message.trim()
        if (trimmed.isEmpty()) {
            return
        }
        val systemMessage = ChatMessage(
            id = nextMessageId++,
            role = ChatRole.SYSTEM,
            content = trimmed,
            timestampMillis = System.currentTimeMillis(),
            isStreaming = false,
        )
        _uiState.update { it.copy(messages = it.messages + systemMessage) }
    }

    private fun scheduleReconnect() {
        if (reconnectJob?.isActive == true) {
            return
        }
        reconnectJob = viewModelScope.launch {
            delay(RECONNECT_DELAY_MS)
            repository.connectGemini()
        }
    }
}
