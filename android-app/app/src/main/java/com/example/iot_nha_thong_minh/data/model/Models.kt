package com.example.iot_nha_thong_minh.data.model

data class Light(
    val location: String,
    val isOn: Boolean,
)

enum class ChatRole { USER, ASSISTANT, SYSTEM }

data class ChatMessage(
    val id: Long,
    val role: ChatRole,
    val content: String,
    val timestampMillis: Long,
    val isStreaming: Boolean = false,
    val imageData: ByteArray? = null,
    val imageMimeType: String? = null,
)

enum class PlaybackStatus { PLAYING, PAUSED, STOPPED }

data class MusicPlaybackState(
    val requestedTitle: String?,
    val matchedSong: String?,
    val status: PlaybackStatus,
    val positionSeconds: Double,
    val durationSeconds: Double?,
    val updatedAtEpochSeconds: Double,
)
