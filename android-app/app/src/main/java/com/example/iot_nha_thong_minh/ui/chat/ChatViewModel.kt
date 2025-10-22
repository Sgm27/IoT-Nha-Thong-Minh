package com.example.iot_nha_thong_minh.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.ChatRole
import com.example.iot_nha_thong_minh.data.model.toMessages
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ChatUiState(
    val isListening: Boolean = false,
    val isSending: Boolean = false,
    val messages: List<ChatMessage> = emptyList(),
    val lastSuggestions: List<String> = emptyList(),
    val errorMessage: String? = null,
)

class ChatViewModel(private val repository: SmartHomeRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private var nextMessageId = 1L

    fun toggleMicrophone() {
        _uiState.update { it.copy(isListening = !it.isListening, errorMessage = null) }
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
        )

        _uiState.update { state ->
            state.copy(
                isSending = true,
                errorMessage = null,
                messages = state.messages + userMessage,
            )
        }

        viewModelScope.launch {
            try {
                val response = repository.sendChat(trimmed)
                val assistantMessages = response.toMessages(nextMessageId)
                nextMessageId += assistantMessages.size
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        messages = state.messages + assistantMessages,
                        lastSuggestions = response.suggestions,
                    )
                }
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        errorMessage = error.message ?: "Không thể gửi tin nhắn",
                        lastSuggestions = emptyList(),
                    )
                }
            }
        }
    }
}
