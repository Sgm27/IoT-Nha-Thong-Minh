package com.example.iot_nha_thong_minh.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface SmartHomeApi {
    @GET("smart-home/lights")
    suspend fun getLights(): List<LightDto>

    @POST("smart-home/lights/on")
    suspend fun turnOnLight(@Body request: LightRequestDto): LightDto

    @POST("smart-home/lights/off")
    suspend fun turnOffLight(@Body request: LightRequestDto): LightDto

    @POST("smart-home/lights/all/on")
    suspend fun turnOnAllLights(): List<LightDto>

    @POST("smart-home/lights/all/off")
    suspend fun turnOffAllLights(): List<LightDto>

    @GET("smart-home/doors")
    suspend fun getDoors(): List<DoorDto>

    @POST("smart-home/doors/open")
    suspend fun openDoor(@Body request: DoorRequestDto): DoorDto

    @POST("smart-home/doors/close")
    suspend fun closeDoor(@Body request: DoorRequestDto): DoorDto

    @GET("smart-home/music/library")
    suspend fun getMusicLibrary(): List<String>

    @POST("smart-home/music/play")
    suspend fun playMusic(@Body request: MusicRequestDto): MusicPlayResponseDto

    @GET("smart-home/music/state")
    suspend fun getMusicState(): MusicPlaybackStateDto

    @POST("smart-home/music/pause")
    suspend fun pauseMusic(): MusicPlaybackStateDto

    @POST("smart-home/music/resume")
    suspend fun resumeMusic(): MusicPlaybackStateDto

    @POST("smart-home/music/seek")
    suspend fun seekMusic(@Body request: MusicSeekRequestDto): MusicPlaybackStateDto

    @POST("assistant/chat")
    suspend fun sendChat(@Body request: ChatRequestDto): ChatResponseDto
}

@Serializable
data class LightDto(
    val location: String,
    @SerialName("is_on")
    val isOn: Boolean,
)

@Serializable
data class LightRequestDto(val location: String)

@Serializable
data class MusicRequestDto(val title: String)

@Serializable
data class MusicSeekRequestDto(
    @SerialName("position_seconds")
    val positionSeconds: Double,
)

@Serializable
data class MusicPlayResponseDto(
    @SerialName("selected_song")
    val selectedSong: String,
    @SerialName("stream_url")
    val streamUrl: String,
    @SerialName("playback_state")
    val playbackState: MusicPlaybackStateDto,
)

@Serializable
data class MusicPlaybackStateDto(
    @SerialName("requested_title")
    val requestedTitle: String? = null,
    @SerialName("matched_song")
    val matchedSong: String? = null,
    val status: String,
    @SerialName("position_seconds")
    val positionSeconds: Double,
    @SerialName("duration_seconds")
    val durationSeconds: Double? = null,
    @SerialName("updated_at")
    val updatedAt: Double,
)

@Serializable
data class ChatRequestDto(val message: String)

@Serializable
data class ChatResponseDto(
    val reply: String,
    val timestamp: String,
    val suggestions: List<String> = emptyList(),
)

@Serializable
data class LightStreamMessageDto(
    val type: String,
    val lights: List<LightDto>? = null,
    val light: LightDto? = null,
)

@Serializable
data class MusicStreamMessageDto(
    val type: String,
    val state: MusicPlaybackStateDto? = null,
)

@Serializable
data class DoorDto(
    val location: String,
    @SerialName("is_open")
    val isOpen: Boolean,
    val angle: Float,
)

@Serializable
data class DoorRequestDto(val location: String)

@Serializable
data class DoorStreamMessageDto(
    val type: String,
    val doors: List<DoorDto>? = null,
    val door: DoorDto? = null,
)
