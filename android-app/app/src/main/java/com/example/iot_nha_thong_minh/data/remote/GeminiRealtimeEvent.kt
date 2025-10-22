package com.example.iot_nha_thong_minh.data.remote

data class GeminiRealtimeTranscription(
    val sender: String,
    val text: String,
    val finished: Boolean,
)

data class GeminiRealtimeAudio(
    val data: ByteArray,
    val mimeType: String?,
    val sampleRate: Int?,
)

sealed class GeminiRealtimeEvent {
    data class Connected(val message: String? = null) : GeminiRealtimeEvent()
    data class Disconnected(val reason: String? = null) : GeminiRealtimeEvent()
    data class SetupComplete(val message: String? = null) : GeminiRealtimeEvent()
    data class Text(val text: String) : GeminiRealtimeEvent()
    data class Transcription(val transcription: GeminiRealtimeTranscription) : GeminiRealtimeEvent()
    data class Audio(val payload: GeminiRealtimeAudio) : GeminiRealtimeEvent()
    data class ConnectionError(val message: String) : GeminiRealtimeEvent()
    data class ToolCall(val functionName: String?) : GeminiRealtimeEvent()
    data class ScreenNavigation(val action: String?) : GeminiRealtimeEvent()
    data class MemoryUpdate(val description: String?) : GeminiRealtimeEvent()
    data class SmartHomeLightUpdate(val location: String, val isOn: Boolean) : GeminiRealtimeEvent()
    data class SmartHomeMusic(
        val requestedTitle: String?,
        val matchedSong: String?,
        val streamUrl: String?,
    ) : GeminiRealtimeEvent()
    data class SmartHomeMusicControl(
        val action: String?,
        val status: String?,
        val requestedTitle: String?,
        val matchedSong: String?,
    ) : GeminiRealtimeEvent()
}
