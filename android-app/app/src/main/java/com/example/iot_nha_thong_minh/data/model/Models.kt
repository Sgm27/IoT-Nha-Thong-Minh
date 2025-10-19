package com.example.iot_nha_thong_minh.data.model

data class Light(
    val location: String,
    val isOn: Boolean,
)

enum class ChatRole { USER, ASSISTANT }

data class ChatMessage(
    val id: Long,
    val role: ChatRole,
    val content: String,
    val timestampMillis: Long,
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
