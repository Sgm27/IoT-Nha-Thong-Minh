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

// Motor/Fan control models
enum class MotorAction {
    ON, OFF, FORWARD, BACKWARD, STOP;

    companion object {
        fun fromString(value: String): MotorAction = when (value.lowercase()) {
            "on" -> ON
            "off" -> OFF
            "forward" -> FORWARD
            "backward" -> BACKWARD
            "stop" -> STOP
            else -> STOP
        }
    }
}

data class Motor(
    val name: String,
    val action: MotorAction,
    val speed: Float, // 0.0 to 1.0
    val updatedAtMillis: Long = System.currentTimeMillis(),
) {
    val isRunning: Boolean
        get() = action == MotorAction.ON || action == MotorAction.FORWARD || action == MotorAction.BACKWARD

    val speedPercent: Int
        get() = (speed * 100).toInt()
}

// Fire detection models
data class FireAlert(
    val id: Long,
    val message: String,
    val confidence: Double?,
    val fireRegions: Int?,
    val firePercentage: Double?,
    val totalFireArea: Int?,
    val triggeredAt: String?,
    val timestampMillis: Long = System.currentTimeMillis(),
    val isAcknowledged: Boolean = false,
)
