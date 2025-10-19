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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.example.iot_nha_thong_minh.data.model.PlaybackStatus
import kotlin.math.abs

@Composable
fun MusicScreen(viewModel: MusicViewModel, modifier: Modifier = Modifier) {
    val uiState = viewModel.uiState.collectAsStateWithLifecycle().value
    val context = LocalContext.current
    val exoPlayer = remember {
        ExoPlayer.Builder(context).build().apply {
            playWhenReady = true
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            exoPlayer.release()
        }
    }

    LaunchedEffect(uiState.currentStreamUrl) {
        val url = uiState.currentStreamUrl
        if (url == null) {
            exoPlayer.stop()
            exoPlayer.clearMediaItems()
        } else {
            val current = exoPlayer.currentMediaItem?.localConfiguration?.uri?.toString()
            if (current != url) {
                exoPlayer.setMediaItem(MediaItem.fromUri(url))
                exoPlayer.prepare()
            }
        }
    }

    LaunchedEffect(uiState.playbackState?.status, uiState.playbackPosition) {
        val state = uiState.playbackState ?: return@LaunchedEffect
        val targetMs = (uiState.playbackPosition * 1000).toLong()
        if (abs(exoPlayer.currentPosition - targetMs) > 1000) {
            exoPlayer.seekTo(targetMs)
        }
        when (state.status) {
            PlaybackStatus.PLAYING -> {
                exoPlayer.playWhenReady = true
                if (!exoPlayer.isPlaying) {
                    exoPlayer.play()
                }
            }
            PlaybackStatus.PAUSED, PlaybackStatus.STOPPED -> {
                if (exoPlayer.isPlaying) {
                    exoPlayer.pause()
                }
            }
        }
    }

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

        AndroidView(
            factory = { ctx -> PlayerView(ctx).apply { player = exoPlayer } },
            modifier = Modifier.fillMaxWidth(),
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
