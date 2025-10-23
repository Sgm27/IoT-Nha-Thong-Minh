package com.example.iot_nha_thong_minh.ui.chat

import android.Manifest
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconToggleButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.ChatRole
import java.io.ByteArrayOutputStream

@Composable
fun ChatScreen(viewModel: ChatViewModel, modifier: Modifier = Modifier) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    var messageInput by rememberSaveable { mutableStateOf("") }
    val listState = rememberLazyListState()

    val context = LocalContext.current
    val audioRecorder = remember { GeminiAudioRecorder() }
    val isRecorderSupported = remember { audioRecorder.isSupported }
    var hasMicPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED,
        )
    }
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED,
        )
    }
    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicturePreview(),
    ) { bitmap ->
        if (bitmap == null) {
            return@rememberLauncherForActivityResult
        }
        val outputStream = ByteArrayOutputStream()
        val compressed = runCatching {
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, outputStream)
        }.getOrDefault(false)
        if (!compressed) {
            viewModel.showError("Không thể xử lý ảnh vừa chụp.")
            return@rememberLauncherForActivityResult
        }
        val imageBytes = outputStream.toByteArray()
        if (imageBytes.isEmpty()) {
            viewModel.showError("Không thể xử lý ảnh vừa chụp.")
            return@rememberLauncherForActivityResult
        }
        viewModel.sendImage(imageBytes, "image/jpeg")
    }
    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        hasCameraPermission = granted
        if (granted) {
            cameraLauncher.launch(null)
        } else {
            viewModel.showError("Ứng dụng cần quyền camera để chụp và gửi ảnh.")
        }
    }
    val micPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        hasMicPermission = granted
        if (granted) {
            viewModel.onMicrophonePermissionGranted()
            if (isRecorderSupported) {
                viewModel.startListening()
            } else {
                viewModel.onSpeechError("Thiết bị của bạn không hỗ trợ trò chuyện bằng giọng nói realtime.")
            }
        } else {
            viewModel.onMicrophonePermissionDenied()
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            audioRecorder.stop()
            audioRecorder.release()
        }
    }

    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.lastIndex)
        }
    }

    LaunchedEffect(uiState.isListening, hasMicPermission) {
        if (uiState.isListening && hasMicPermission) {
            if (!isRecorderSupported) {
                viewModel.onSpeechError("Thiết bị của bạn không hỗ trợ trò chuyện bằng giọng nói realtime.")
                viewModel.stopListening()
                return@LaunchedEffect
            }
            val started = audioRecorder.start(
                onChunk = { chunk ->
                    viewModel.sendAudioChunk(chunk, audioRecorder.sampleRate)
                },
                onError = { errorMessage ->
                    viewModel.onSpeechError(errorMessage)
                    viewModel.stopListening()
                },
            )
            if (!started) {
                viewModel.stopListening()
            }
        } else {
            audioRecorder.stop()
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        StatusCard(isConnected = uiState.isConnected, statusMessage = uiState.statusMessage)

        ElevatedCard(modifier = Modifier.weight(1f).fillMaxWidth()) {
            if (uiState.messages.isEmpty()) {
                Column(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text(
                        "Hãy bắt đầu cuộc trò chuyện với trợ lý AI.",
                        style = MaterialTheme.typography.bodyLarge,
                        textAlign = TextAlign.Center,
                    )
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

        if (!isRecorderSupported) {
            Text(
                "Thiết bị của bạn không hỗ trợ trò chuyện bằng giọng nói realtime.",
                color = MaterialTheme.colorScheme.error,
            )
        } else if (uiState.isMicPermissionDenied && !hasMicPermission) {
            Text(
                "Vui lòng cấp quyền micro để trò chuyện bằng giọng nói.",
                color = MaterialTheme.colorScheme.error,
            )
        }

        uiState.errorMessage?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
        }

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                IconToggleButton(
                    modifier = Modifier.size(56.dp),
                    checked = uiState.isListening,
                    onCheckedChange = { enabled ->
                        if (!uiState.isConnected) {
                            viewModel.onSpeechError("Đang kết nối tới Gemini, vui lòng đợi...")
                            return@IconToggleButton
                        }
                        if (enabled) {
                            if (!isRecorderSupported) {
                                viewModel.onSpeechError("Thiết bị của bạn không hỗ trợ trò chuyện bằng giọng nói realtime.")
                            } else if (!hasMicPermission) {
                                micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            } else {
                                viewModel.onMicrophonePermissionGranted()
                                viewModel.onListeningToggleRequested(true)
                            }
                        } else {
                            viewModel.onListeningToggleRequested(false)
                        }
                    },
                    enabled = uiState.isConnected && isRecorderSupported,
                ) {
                    Icon(
                        imageVector = if (uiState.isListening) Icons.Default.Mic else Icons.Default.MicOff,
                        contentDescription = null,
                    )
                }
                Text(
                    text = if (uiState.isListening) "Đang lắng nghe" else "Nhấn để nói",
                    style = MaterialTheme.typography.labelSmall,
                )
            }

            OutlinedTextField(
                modifier = Modifier.weight(1f),
                value = messageInput,
                onValueChange = { messageInput = it },
                label = { Text("Nhập tin nhắn") },
                singleLine = true,
                enabled = uiState.isConnected,
            )

            IconButton(
                onClick = {
                    if (!uiState.isConnected) {
                        viewModel.showError("Đang kết nối tới Gemini, vui lòng đợi...")
                        return@IconButton
                    }
                    if (!hasCameraPermission) {
                        cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                    } else {
                        cameraLauncher.launch(null)
                    }
                },
                enabled = uiState.isConnected,
            ) {
                Icon(Icons.Default.CameraAlt, contentDescription = "Chụp ảnh gửi Gemini")
            }

            Button(
                onClick = {
                    if (messageInput.isNotBlank()) {
                        viewModel.sendMessage(messageInput)
                        messageInput = ""
                    }
                },
                enabled = messageInput.isNotBlank() && uiState.isConnected,
            ) {
                Icon(Icons.Default.Send, contentDescription = null)
            }
        }
    }
}

@Composable
private fun StatusCard(isConnected: Boolean, statusMessage: String) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text("Trạng thái kết nối", style = MaterialTheme.typography.titleSmall)
                Text(statusMessage, style = MaterialTheme.typography.bodyMedium)
            }
            val indicatorColor: Color = if (isConnected) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.tertiary
            }
            Box(
                modifier = Modifier
                    .size(16.dp)
                    .clip(CircleShape)
                    .background(indicatorColor),
            )
        }
    }
}

@Composable
private fun MessageBubble(message: ChatMessage) {
    val (background, alignment) = when (message.role) {
        ChatRole.USER -> MaterialTheme.colorScheme.surfaceVariant to Alignment.End
        ChatRole.ASSISTANT -> MaterialTheme.colorScheme.primaryContainer to Alignment.Start
        ChatRole.SYSTEM -> MaterialTheme.colorScheme.secondaryContainer to Alignment.CenterHorizontally
    }
    val textAlign = when (message.role) {
        ChatRole.USER -> TextAlign.End
        ChatRole.SYSTEM -> TextAlign.Center
        else -> TextAlign.Start
    }
    val imageBitmap = remember(message.id, message.imageData) {
        message.imageData?.takeIf { it.isNotEmpty() }?.let { data ->
            runCatching {
                BitmapFactory.decodeByteArray(data, 0, data.size)?.asImageBitmap()
            }.getOrNull()
        }
    }
    val imageAspectRatio = imageBitmap?.let { bitmap ->
        if (bitmap.width > 0 && bitmap.height > 0) {
            bitmap.width.toFloat() / bitmap.height.toFloat()
        } else {
            null
        }
    }
    Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = alignment) {
        Card(colors = CardDefaults.cardColors(containerColor = background)) {
            Column(
                modifier = Modifier.padding(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                imageBitmap?.let { bitmap ->
                    val modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .let { base ->
                            imageAspectRatio?.let { ratio ->
                                if (!ratio.isNaN() && !ratio.isInfinite() && ratio > 0f) {
                                    base.aspectRatio(ratio)
                                } else {
                                    base.heightIn(max = 240.dp)
                                }
                            } ?: base.heightIn(max = 240.dp)
                        }
                    Image(
                        bitmap = bitmap,
                        contentDescription = "Ảnh trong hội thoại",
                        modifier = modifier,
                        contentScale = ContentScale.Crop,
                    )
                    if (message.content.isNotBlank()) {
                        Spacer(modifier = Modifier.height(8.dp))
                    }
                }
                if (message.content.isNotBlank()) {
                    Text(
                        text = message.content,
                        style = if (message.isStreaming) {
                            MaterialTheme.typography.bodyMedium.copy(fontStyle = FontStyle.Italic)
                        } else {
                            MaterialTheme.typography.bodyMedium
                        },
                        textAlign = textAlign,
                    )
                }
            }
        }
    }
}
