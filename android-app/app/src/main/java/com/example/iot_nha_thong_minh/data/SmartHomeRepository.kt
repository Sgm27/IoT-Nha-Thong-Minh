package com.example.iot_nha_thong_minh.data

import android.util.Log
import com.example.iot_nha_thong_minh.data.remote.ChatRequestDto
import com.example.iot_nha_thong_minh.data.remote.ChatResponseDto
import com.example.iot_nha_thong_minh.data.remote.LightDto
import com.example.iot_nha_thong_minh.data.remote.LightRequestDto
import com.example.iot_nha_thong_minh.data.remote.LightStreamMessageDto
import com.example.iot_nha_thong_minh.data.remote.MusicPlaybackStateDto
import com.example.iot_nha_thong_minh.data.remote.MusicPlayResponseDto
import com.example.iot_nha_thong_minh.data.remote.MusicRequestDto
import com.example.iot_nha_thong_minh.data.remote.MusicSeekRequestDto
import com.example.iot_nha_thong_minh.data.remote.MusicStreamMessageDto
import com.example.iot_nha_thong_minh.data.remote.SmartHomeApi
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener

private const val BASE_WS_URL = "wss://iot.sonktx.online"

class SmartHomeRepository(
    private val api: SmartHomeApi,
    private val okHttpClient: OkHttpClient,
    private val json: Json,
) {
    suspend fun fetchLights(): List<LightDto> = api.getLights()

    suspend fun toggleLight(location: String, turnOn: Boolean): LightDto =
        if (turnOn) api.turnOnLight(LightRequestDto(location)) else api.turnOffLight(LightRequestDto(location))

    fun observeLights(): Flow<LightStreamMessageDto> = callbackFlow {
        val request = Request.Builder()
            .url("$BASE_WS_URL/smart-home/lights/stream")
            .build()

        val listener = object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = json.decodeFromString(LightStreamMessageDto.serializer(), text)
                    trySend(message)
                } catch (error: Throwable) {
                    Log.e("SmartHomeRepository", "Failed to parse light stream", error)
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                close(t)
            }
        }

        val socket = okHttpClient.newWebSocket(request, listener)
        awaitClose { socket.cancel() }
    }

    suspend fun fetchMusicLibrary(): List<String> = api.getMusicLibrary()

    suspend fun requestPlayMusic(title: String): MusicPlayResponseDto = api.playMusic(MusicRequestDto(title))

    suspend fun fetchMusicState(): MusicPlaybackStateDto = api.getMusicState()

    suspend fun pauseMusic(): MusicPlaybackStateDto = api.pauseMusic()

    suspend fun resumeMusic(): MusicPlaybackStateDto = api.resumeMusic()

    suspend fun seekMusic(positionSeconds: Double): MusicPlaybackStateDto =
        api.seekMusic(MusicSeekRequestDto(positionSeconds))

    fun observeMusicUpdates(): Flow<MusicStreamMessageDto> = callbackFlow {
        val request = Request.Builder()
            .url("$BASE_WS_URL/smart-home/music/updates")
            .build()

        val listener = object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = json.decodeFromString(MusicStreamMessageDto.serializer(), text)
                    trySend(message)
                } catch (error: Throwable) {
                    Log.e("SmartHomeRepository", "Failed to parse music stream", error)
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                close(t)
            }
        }

        val socket = okHttpClient.newWebSocket(request, listener)
        awaitClose { socket.cancel() }
    }

    suspend fun sendChat(message: String): ChatResponseDto = api.sendChat(ChatRequestDto(message))
}
