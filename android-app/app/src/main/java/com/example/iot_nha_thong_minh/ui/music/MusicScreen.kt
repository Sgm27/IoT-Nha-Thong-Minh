package com.example.iot_nha_thong_minh.ui.music

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.iot_nha_thong_minh.data.model.PlaybackStatus

@Composable
fun MusicScreen(viewModel: MusicViewModel, modifier: Modifier = Modifier) {
    val uiState = viewModel.uiState.collectAsStateWithLifecycle().value

    var songTitle by rememberSaveable { mutableStateOf("") }

    Column(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        uiState.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        uiState.infoMessage?.let { Text(it, color = MaterialTheme.colorScheme.primary) }

        Card {
            Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Trạng thái phát nhạc", style = MaterialTheme.typography.titleMedium)
                Text(
                    text = when (uiState.playbackState?.status) {
                        PlaybackStatus.PLAYING -> "Đang phát: ${uiState.playbackState.matchedSong ?: ""}"
                        PlaybackStatus.PAUSED -> "Đang tạm dừng: ${uiState.playbackState.matchedSong ?: ""}"
                        PlaybackStatus.STOPPED -> "Đã dừng phát nhạc"
                        null -> "Chưa có trạng thái nhạc"
                    },
                    fontWeight = FontWeight.SemiBold,
                )

                val durationSeconds = uiState.playbackState?.durationSeconds ?: 0.0
                val sliderRange = if (durationSeconds > 0) 0f..durationSeconds.toFloat() else 0f..(uiState.playbackPosition + 1.0).toFloat()
                var sliderPosition by remember(uiState.playbackState?.matchedSong) {
                    mutableStateOf(uiState.playbackPosition.toFloat())
                }
                LaunchedEffect(uiState.playbackPosition) {
                    sliderPosition = uiState.playbackPosition.toFloat().coerceIn(sliderRange.start, sliderRange.endInclusive)
                }
                Slider(
                    value = sliderPosition,
                    onValueChange = { sliderPosition = it },
                    valueRange = sliderRange,
                    onValueChangeFinished = { viewModel.seekTo(sliderPosition.toDouble()) },
                )

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { viewModel.resume() }, enabled = uiState.playbackState?.status == PlaybackStatus.PAUSED) {
                        Icon(Icons.Default.PlayArrow, contentDescription = null)
                        Text("Tiếp tục", modifier = Modifier.padding(start = 4.dp))
                    }
                    Button(onClick = { viewModel.pause() }, enabled = uiState.playbackState?.status == PlaybackStatus.PLAYING) {
                        Icon(Icons.Default.Pause, contentDescription = null)
                        Text("Tạm dừng", modifier = Modifier.padding(start = 4.dp))
                    }
                }
            }
        }

        Text(
            modifier = Modifier.fillMaxWidth(),
            text = "Âm thanh sẽ phát trên máy chủ trung tâm. Ứng dụng đóng vai trò điều khiển từ xa.",
            textAlign = TextAlign.Center,
            style = MaterialTheme.typography.bodyMedium,
        )

        OutlinedTextField(
            value = songTitle,
            onValueChange = { songTitle = it },
            label = { Text("Tên bài hát") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = {
            viewModel.playSong(songTitle)
            songTitle = ""
        }, enabled = songTitle.isNotBlank()) {
            Text("Phát bài hát")
        }

        Text("Thư viện nhạc", style = MaterialTheme.typography.titleMedium)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(uiState.library) { item ->
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(item)
                        Button(onClick = {
                            songTitle = item
                            viewModel.playSong(item)
                        }) {
                            Text("Phát")
                        }
                    }
                }
            }
        }
    }
}
