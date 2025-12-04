package com.example.iot_nha_thong_minh.data

import android.util.Log
import com.example.iot_nha_thong_minh.data.local.ChatMessageDao
import com.example.iot_nha_thong_minh.data.local.ChatMessageEntity
import com.example.iot_nha_thong_minh.data.local.FireAlertDao
import com.example.iot_nha_thong_minh.data.local.FireAlertEntity
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.FireAlert
import com.example.iot_nha_thong_minh.data.remote.DoorDto
import com.example.iot_nha_thong_minh.data.remote.DoorRequestDto
import com.example.iot_nha_thong_minh.data.remote.DoorStreamMessageDto
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeEvent
import com.example.iot_nha_thong_minh.data.remote.GeminiWebSocketClient
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
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener

class SmartHomeRepository(
    private val api: SmartHomeApi,
    private val okHttpClient: OkHttpClient,
    private val json: Json,
    private val chatMessageDao: ChatMessageDao? = null,
    private val fireAlertDao: FireAlertDao? = null,
) {
    private val geminiClient = GeminiWebSocketClient(okHttpClient, json)

    val geminiEvents: SharedFlow<GeminiRealtimeEvent> = geminiClient.events

    suspend fun fetchLights(): List<LightDto> = api.getLights()

    suspend fun toggleLight(location: String, turnOn: Boolean): LightDto =
        if (turnOn) api.turnOnLight(LightRequestDto(location)) else api.turnOffLight(LightRequestDto(location))

    suspend fun turnOnAllLights(): List<LightDto> = api.turnOnAllLights()

    suspend fun turnOffAllLights(): List<LightDto> = api.turnOffAllLights()

    suspend fun fetchDoors(): List<DoorDto> = api.getDoors()

    suspend fun openDoor(location: String): DoorDto = api.openDoor(DoorRequestDto(location))

    suspend fun closeDoor(location: String): DoorDto = api.closeDoor(DoorRequestDto(location))

    fun observeLights(): Flow<LightStreamMessageDto> = callbackFlow {
        val request = Request.Builder()
            .url("${EnvironmentConfig.wsBaseUrl}/smart-home/lights/stream")
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
            .url("${EnvironmentConfig.wsBaseUrl}/smart-home/music/updates")
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

    fun observeDoors(): Flow<DoorStreamMessageDto> = callbackFlow {
        val request = Request.Builder()
            .url("${EnvironmentConfig.wsBaseUrl}/smart-home/doors/stream")
            .build()

        val listener = object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = json.decodeFromString(DoorStreamMessageDto.serializer(), text)
                    trySend(message)
                } catch (error: Throwable) {
                    Log.e("SmartHomeRepository", "Failed to parse door stream", error)
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                close(t)
            }
        }

        val socket = okHttpClient.newWebSocket(request, listener)
        awaitClose { socket.cancel() }
    }

    fun connectGemini() {
        geminiClient.connect()
    }

    fun disconnectGemini() {
        geminiClient.disconnect()
    }

    fun sendGeminiText(message: String): Boolean = geminiClient.sendText(message)

    fun sendGeminiRealtimeAudio(data: ByteArray, sampleRate: Int): Boolean =
        geminiClient.sendRealtimeAudio(data, sampleRate)

    fun sendGeminiImage(imageData: ByteArray, mimeType: String): Boolean =
        geminiClient.sendRealtimeImage(imageData, mimeType)

    // Chat message persistence
    fun observeChatMessages(limit: Int = 100): Flow<List<ChatMessage>>? =
        chatMessageDao?.getRecentMessages(limit)?.map { entities ->
            entities.map { it.toDomain() }.reversed()
        }

    suspend fun saveChatMessage(message: ChatMessage): Long? =
        chatMessageDao?.insertMessage(ChatMessageEntity.fromDomain(message))

    suspend fun saveChatMessages(messages: List<ChatMessage>) {
        chatMessageDao?.insertMessages(messages.map { ChatMessageEntity.fromDomain(it) })
    }

    suspend fun clearChatHistory() {
        chatMessageDao?.clearAllMessages()
    }

    // Fire alert persistence
    fun observeFireAlerts(limit: Int = 100): Flow<List<FireAlert>>? =
        fireAlertDao?.getRecentAlerts(limit)?.map { entities ->
            entities.map { it.toDomain() }
        }

    fun observeUnacknowledgedCount(): Flow<Int>? =
        fireAlertDao?.getUnacknowledgedCount()

    suspend fun saveFireAlert(alert: FireAlert): Long? =
        fireAlertDao?.insertAlert(FireAlertEntity.fromDomain(alert))

    suspend fun acknowledgeFireAlert(alertId: Long) {
        fireAlertDao?.acknowledgeAlert(alertId)
    }

    suspend fun acknowledgeAllFireAlerts() {
        fireAlertDao?.acknowledgeAllAlerts()
    }

    suspend fun clearFireAlertHistory() {
        fireAlertDao?.clearAllAlerts()
    }
}
