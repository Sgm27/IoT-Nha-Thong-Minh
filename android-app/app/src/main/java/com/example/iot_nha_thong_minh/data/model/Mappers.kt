package com.example.iot_nha_thong_minh.data.model

import com.example.iot_nha_thong_minh.data.remote.ChatResponseDto
import com.example.iot_nha_thong_minh.data.remote.LightDto
import com.example.iot_nha_thong_minh.data.remote.LightStreamMessageDto
import com.example.iot_nha_thong_minh.data.remote.MusicPlaybackStateDto
import com.example.iot_nha_thong_minh.data.remote.MusicStreamMessageDto

fun LightDto.toDomain(): Light = Light(location = location, isOn = isOn)

fun MusicPlaybackStateDto.toDomain(): MusicPlaybackState {
    val status = when (status.lowercase()) {
        "playing" -> PlaybackStatus.PLAYING
        "paused" -> PlaybackStatus.PAUSED
        else -> PlaybackStatus.STOPPED
    }
    return MusicPlaybackState(
        requestedTitle = requestedTitle,
        matchedSong = matchedSong,
        status = status,
        positionSeconds = positionSeconds,
        durationSeconds = durationSeconds,
        updatedAtEpochSeconds = updatedAt,
    )
}

fun ChatResponseDto.toMessages(nextId: Long): List<ChatMessage> = buildList {
    add(
        ChatMessage(
            id = nextId,
            role = ChatRole.ASSISTANT,
            content = reply,
            timestampMillis = System.currentTimeMillis(),
            isStreaming = false,
        )
    )
}

fun LightStreamMessageDto.toLightUpdates(): List<Light> = when (type) {
    "snapshot" -> lights.orEmpty().map { it.toDomain() }
    "update" -> light?.let { listOf(it.toDomain()) } ?: emptyList()
    else -> emptyList()
}

fun MusicStreamMessageDto.toPlaybackState(): MusicPlaybackState? = state?.toDomain()
