package com.example.iot_nha_thong_minh.data.remote

import android.util.Base64
import android.util.Log
import com.example.iot_nha_thong_minh.data.EnvironmentConfig
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

private const val DEFAULT_AUDIO_SAMPLE_RATE = 16_000

class GeminiWebSocketClient(
    private val okHttpClient: OkHttpClient,
    private val json: Json,
) {
    private val isConnecting = AtomicBoolean(false)
    private var webSocket: WebSocket? = null

    private val _events = MutableSharedFlow<GeminiRealtimeEvent>(
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    val events: SharedFlow<GeminiRealtimeEvent> = _events

    fun connect() {
        if (webSocket != null || !isConnecting.compareAndSet(false, true)) {
            return
        }

        val request = Request.Builder()
            .url(EnvironmentConfig.geminiWsUrl)
            .build()

        okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                this@GeminiWebSocketClient.webSocket = webSocket
                isConnecting.set(false)
                _events.tryEmit(GeminiRealtimeEvent.Connected())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(webSocket, text)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                if (this@GeminiWebSocketClient.webSocket == webSocket) {
                    this@GeminiWebSocketClient.webSocket = null
                }
                isConnecting.set(false)
                _events.tryEmit(GeminiRealtimeEvent.Disconnected(reason.takeIf { it.isNotBlank() }))
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("GeminiWebSocket", "Connection failure", t)
                if (this@GeminiWebSocketClient.webSocket == webSocket) {
                    this@GeminiWebSocketClient.webSocket = null
                }
                isConnecting.set(false)
                _events.tryEmit(GeminiRealtimeEvent.ConnectionError(t.message ?: "Không thể kết nối tới Gemini"))
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, "Client closed")
        webSocket = null
        isConnecting.set(false)
    }

    fun sendText(text: String): Boolean {
        val payload = buildJsonObject { put("text", text) }
        return sendRaw(json.encodeToString(JsonObject.serializer(), payload))
    }

    fun sendKeepAlive() {
        val timestamp = DateTimeFormatter.ISO_INSTANT.format(Instant.now())
        val payload = "{" + "\"keepalive\":{" + "\"timestamp\":\"$timestamp\"" + "}}"
        sendRaw(payload)
    }

    fun sendRealtimeAudio(data: ByteArray, sampleRate: Int): Boolean {
        val mimeSampleRate = if (sampleRate > 0) sampleRate else DEFAULT_AUDIO_SAMPLE_RATE
        return sendRealtimeMediaChunk(data, "audio/pcm;rate=$mimeSampleRate")
    }

    fun sendRealtimeImage(data: ByteArray, mimeType: String): Boolean {
        val normalizedMime = mimeType.takeIf { it.isNotBlank() } ?: "image/jpeg"
        return sendRealtimeMediaChunk(data, normalizedMime)
    }

    private fun sendRealtimeMediaChunk(data: ByteArray, mimeType: String): Boolean {
        if (data.isEmpty()) {
            return false
        }
        val encoded = try {
            Base64.encodeToString(data, Base64.NO_WRAP)
        } catch (error: IllegalArgumentException) {
            Log.e("GeminiWebSocket", "Không thể mã hóa dữ liệu media", error)
            return false
        }
        val safeMimeType = mimeType.takeIf { it.isNotBlank() } ?: "application/octet-stream"
        val payload = buildJsonObject {
            put(
                "realtime_input",
                buildJsonObject {
                    put(
                        "media_chunks",
                        buildJsonArray {
                            add(
                                buildJsonObject {
                                    put("mime_type", safeMimeType)
                                    put("data", encoded)
                                },
                            )
                        },
                    )
                },
            )
        }
        return sendRaw(json.encodeToString(JsonObject.serializer(), payload))
    }

    private fun sendRaw(payload: String): Boolean {
        val socket = webSocket ?: return false
        return try {
            socket.send(payload)
        } catch (error: Exception) {
            Log.e("GeminiWebSocket", "Failed to send payload", error)
            false
        }
    }

    private fun handleMessage(webSocket: WebSocket, text: String) {
        val element = runCatching { json.parseToJsonElement(text) }.getOrNull()
        val obj = element as? JsonObject ?: return

        if ("setupComplete" in obj) {
            _events.tryEmit(GeminiRealtimeEvent.SetupComplete())
            return
        }

        val type = obj["type"]?.jsonPrimitive?.asStringOrNull()
        when (type) {
            "keepalive" -> {
                sendKeepAlive()
                return
            }
            "connection_error" -> {
                val message = obj["message"]?.jsonPrimitive?.asStringOrNull()
                    ?: "Không thể kết nối tới Gemini. Ứng dụng đang chuyển sang chế độ ngoại tuyến."
                _events.tryEmit(GeminiRealtimeEvent.ConnectionError(message))
                return
            }
            "tool_call" -> {
                _events.tryEmit(
                    GeminiRealtimeEvent.ToolCall(
                        obj["function_name"]?.jsonPrimitive?.asStringOrNull(),
                    ),
                )
                return
            }
            "screen_navigation" -> {
                _events.tryEmit(
                    GeminiRealtimeEvent.ScreenNavigation(
                        obj["action"]?.jsonPrimitive?.asStringOrNull(),
                    ),
                )
                return
            }
            "memory_update" -> {
                _events.tryEmit(GeminiRealtimeEvent.MemoryUpdate(null))
                return
            }
            "smart_home_light_update" -> {
                val location = obj["location"]?.jsonPrimitive?.asStringOrNull() ?: ""
                val isOn = obj["is_on"]?.jsonPrimitive?.asBooleanOrNull() ?: false
                _events.tryEmit(GeminiRealtimeEvent.SmartHomeLightUpdate(location, isOn))
                return
            }
            "smart_home_music" -> {
                _events.tryEmit(
                    GeminiRealtimeEvent.SmartHomeMusic(
                        obj["requested_title"]?.jsonPrimitive?.asStringOrNull(),
                        obj["matched_song"]?.jsonPrimitive?.asStringOrNull(),
                        obj["stream_url"]?.jsonPrimitive?.asStringOrNull(),
                    ),
                )
                return
            }
            "smart_home_music_control" -> {
                _events.tryEmit(
                    GeminiRealtimeEvent.SmartHomeMusicControl(
                        obj["action"]?.jsonPrimitive?.asStringOrNull(),
                        obj["status"]?.jsonPrimitive?.asStringOrNull(),
                        obj["requested_title"]?.jsonPrimitive?.asStringOrNull(),
                        obj["matched_song"]?.jsonPrimitive?.asStringOrNull(),
                    ),
                )
                return
            }
            "fire_detection_alert" -> {
                val detection = obj["detection"]?.jsonObject?.let { detectionObj ->
                    GeminiRealtimeFireDetection(
                        detectionObj["confidence"]?.jsonPrimitive?.asDoubleOrNull(),
                        detectionObj["fire_regions"]?.jsonPrimitive?.asIntOrNull(),
                        detectionObj["fire_percentage"]?.jsonPrimitive?.asDoubleOrNull(),
                        detectionObj["total_fire_area"]?.jsonPrimitive?.asIntOrNull(),
                    )
                }
                val audioBase64 = obj["audio_base64"]?.jsonPrimitive?.asStringOrNull()
                val audioFormat = obj["audio_format"]?.jsonPrimitive?.asStringOrNull()
                val audioSampleRate = obj["audio_sample_rate"]?.jsonPrimitive?.asIntOrNull()
                val audio = audioBase64?.let {
                    decodeAudioPayload(it, audioFormat, audioSampleRate)
                }
                val messageText = obj["message"]?.jsonPrimitive?.asStringOrNull()
                    ?: "Cảnh báo cháy!"
                val triggeredAt = obj["triggered_at"]?.jsonPrimitive?.asStringOrNull()
                val sourceMime = obj["source_mime_type"]?.jsonPrimitive?.asStringOrNull()
                _events.tryEmit(
                    GeminiRealtimeEvent.FireAlert(
                        message = messageText,
                        detection = detection,
                        audio = audio,
                        triggeredAt = triggeredAt,
                        sourceMimeType = sourceMime,
                    ),
                )
                return
            }
            "motor_control" -> {
                val name = obj["name"]?.jsonPrimitive?.asStringOrNull() ?: "Quạt"
                val action = obj["action"]?.jsonPrimitive?.asStringOrNull() ?: "stop"
                val speed = obj["speed"]?.jsonPrimitive?.asFloatOrNull() ?: 0f
                _events.tryEmit(GeminiRealtimeEvent.MotorControl(name, action, speed))
                return
            }
        }

        obj["transcription"]?.jsonObject?.let { transcription ->
            val textValue = transcription["text"]?.jsonPrimitive?.asStringOrNull() ?: ""
            val sender = transcription["sender"]?.jsonPrimitive?.asStringOrNull() ?: ""
            val finished = transcription["finished"]?.jsonPrimitive?.asBooleanOrNull() ?: false
            _events.tryEmit(
                GeminiRealtimeEvent.Transcription(
                    GeminiRealtimeTranscription(sender = sender, text = textValue, finished = finished),
                ),
            )
            return
        }

        obj["text"]?.jsonPrimitive?.asStringOrNull()?.let { content ->
            _events.tryEmit(GeminiRealtimeEvent.Text(content))
            return
        }

        obj["audio"]?.let { audioElement ->
            val audioPayload = when {
                audioElement is kotlinx.serialization.json.JsonPrimitive && audioElement.isString -> {
                    decodeAudioPayload(audioElement.content, null, null)
                }
                audioElement is JsonObject -> {
                    val data = audioElement["data"]?.jsonPrimitive?.asStringOrNull()
                    val mime = audioElement["mime_type"]?.jsonPrimitive?.asStringOrNull()
                    val sampleRate = audioElement["sample_rate"]?.jsonPrimitive?.asIntOrNull()
                    if (data != null) {
                        decodeAudioPayload(data, mime, sampleRate)
                    } else {
                        null
                    }
                }
                else -> null
            }
            if (audioPayload != null) {
                _events.tryEmit(GeminiRealtimeEvent.Audio(audioPayload))
            }
        }
    }

    private fun decodeAudioPayload(
        base64Data: String,
        mimeType: String?,
        sampleRate: Int?,
    ): GeminiRealtimeAudio? {
        val bytes = try {
            Base64.decode(base64Data, Base64.DEFAULT)
        } catch (error: IllegalArgumentException) {
            Log.e("GeminiWebSocket", "Failed to decode assistant audio", error)
            return null
        }
        return GeminiRealtimeAudio(data = bytes, mimeType = mimeType, sampleRate = sampleRate)
    }
}

private fun kotlinx.serialization.json.JsonPrimitive?.asStringOrNull(): String? =
    this?.takeIf { it.isString }?.content

private fun kotlinx.serialization.json.JsonPrimitive?.asBooleanOrNull(): Boolean? =
    try {
        this?.booleanOrNull
    } catch (_: Exception) {
        null
    }

private fun kotlinx.serialization.json.JsonPrimitive?.asIntOrNull(): Int? =
    try {
        this?.intOrNull
    } catch (_: Exception) {
        null
    }

private fun kotlinx.serialization.json.JsonPrimitive?.asDoubleOrNull(): Double? =
    try {
        this?.doubleOrNull
    } catch (_: Exception) {
        null
    }

private fun kotlinx.serialization.json.JsonPrimitive?.asFloatOrNull(): Float? =
    try {
        this?.doubleOrNull?.toFloat()
    } catch (_: Exception) {
        null
    }
