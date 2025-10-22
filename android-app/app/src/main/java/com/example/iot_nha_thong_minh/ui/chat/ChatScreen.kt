package com.example.iot_nha_thong_minh.ui.chat

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.IconToggleButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.ChatRole

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ChatScreen(viewModel: ChatViewModel, modifier: Modifier = Modifier) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    var messageInput by rememberSaveable { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.lastIndex)
        }
    }

    Column(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        ElevatedCard(modifier = Modifier.weight(1f).fillMaxWidth()) {
            if (uiState.messages.isEmpty()) {
                Column(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text("Hãy bắt đầu cuộc trò chuyện với trợ lý AI.", style = MaterialTheme.typography.bodyLarge)
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize().padding(16.dp),
                    state = listState,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    items(uiState.messages) { message ->
                        MessageBubble(message)
                    }
                }
            }
        }

        if (uiState.lastSuggestions.isNotEmpty()) {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                FlowRow(
                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    uiState.lastSuggestions.forEach { suggestion ->
                        AssistChip(onClick = {
                            messageInput = suggestion
                        }, label = { Text(suggestion, textAlign = TextAlign.Center) })
                    }
                }
            }
        }

        uiState.errorMessage?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
        }

        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            IconToggleButton(checked = uiState.isListening, onCheckedChange = { viewModel.toggleMicrophone() }) {
                Icon(imageVector = if (uiState.isListening) Icons.Default.Mic else Icons.Default.MicOff, contentDescription = null)
            }
            OutlinedTextField(
                modifier = Modifier.weight(1f),
                value = messageInput,
                onValueChange = { messageInput = it },
                label = { Text("Nhập tin nhắn") },
                singleLine = true,
                enabled = !uiState.isSending,
            )
            Button(onClick = {
                if (messageInput.isNotBlank()) {
                    viewModel.sendMessage(messageInput)
                    messageInput = ""
                }
            }, enabled = messageInput.isNotBlank() && !uiState.isSending) {
                Icon(Icons.Default.Send, contentDescription = null)
            }
        }
    }
}

@Composable
private fun MessageBubble(message: ChatMessage) {
    val isAssistant = message.role == ChatRole.ASSISTANT
    val background = if (isAssistant) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
    val alignment = if (isAssistant) Alignment.Start else Alignment.End
    Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = alignment) {
        Card(colors = CardDefaults.cardColors(containerColor = background)) {
            Text(
                modifier = Modifier.padding(12.dp),
                text = message.content,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
