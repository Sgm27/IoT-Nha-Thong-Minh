package com.example.iot_nha_thong_minh.ui.chat

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.util.Log
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeAudio
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.nio.ByteBuffer
import java.nio.ByteOrder

// Output sample rate from Gemini (24kHz) - same as web frontend
private const val OUTPUT_SAMPLE_RATE = 24_000
private const val BYTES_PER_SAMPLE = 2 // PCM 16-bit = 2 bytes per sample

class GeminiAudioPlayer {
    private data class AudioChunk(val data: ByteArray, val sampleRate: Int)

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val queue = Channel<AudioChunk>(capacity = Channel.UNLIMITED)
    private val audioLock = Any()
    private val playbackMutex = Mutex()

    @Volatile
    private var audioTrack: AudioTrack? = null

    @Volatile
    private var currentSampleRate = OUTPUT_SAMPLE_RATE

    init {
        scope.launch {
            for (chunk in queue) {
                playChunk(chunk)
            }
        }
    }

    fun enqueue(audio: GeminiRealtimeAudio) {
        if (audio.data.isEmpty()) {
            return
        }
        // Gemini output is always 24kHz - use OUTPUT_SAMPLE_RATE as default
        val rate = audio.sampleRate?.takeIf { it > 0 } ?: OUTPUT_SAMPLE_RATE
        scope.launch {
            queue.send(AudioChunk(audio.data, rate))
        }
    }

    fun release() {
        queue.close()
        scope.cancel()
        synchronized(audioLock) {
            audioTrack?.let { track ->
                try {
                    track.stop()
                } catch (_: IllegalStateException) {
                    // Ignore stopping errors
                }
                track.release()
            }
            audioTrack = null
        }
    }

    private suspend fun playChunk(chunk: AudioChunk) {
        playbackMutex.withLock {
            try {
                // Align bytes to 2-byte boundary (same as web frontend)
                val alignedData = alignPcmData(chunk.data)
                if (alignedData.isEmpty()) {
                    return
                }

                ensureTrack(chunk.sampleRate)
                val track = audioTrack ?: return

                // Start playback before writing (streaming mode best practice)
                synchronized(audioLock) {
                    if (track.playState != AudioTrack.PLAYSTATE_PLAYING) {
                        try {
                            track.play()
                        } catch (error: IllegalStateException) {
                            Log.e("GeminiAudioPlayer", "Không thể phát âm thanh", error)
                            return
                        }
                    }
                }

                // Write PCM data using ShortArray for correct byte order handling
                val shortBuffer = convertToShortArray(alignedData)
                if (shortBuffer.isEmpty()) {
                    return
                }

                var offset = 0
                while (offset < shortBuffer.size) {
                    val written = synchronized(audioLock) {
                        try {
                            track.write(
                                shortBuffer,
                                offset,
                                shortBuffer.size - offset,
                                AudioTrack.WRITE_BLOCKING
                            )
                        } catch (error: IllegalStateException) {
                            Log.e("GeminiAudioPlayer", "Không thể ghi dữ liệu âm thanh", error)
                            -1
                        }
                    }
                    if (written < 0) {
                        Log.e("GeminiAudioPlayer", "Lỗi ghi âm thanh: $written")
                        break
                    }
                    if (written == 0) {
                        // Buffer full, wait a bit
                        kotlinx.coroutines.delay(5)
                        continue
                    }
                    offset += written
                }
            } catch (error: Exception) {
                Log.e("GeminiAudioPlayer", "Lỗi khi phát âm thanh của Gemini", error)
            }
        }
    }

    /**
     * Align PCM data to 2-byte boundary (same as web frontend's decodeAudioChunk)
     */
    private fun alignPcmData(data: ByteArray): ByteArray {
        val remainder = data.size % BYTES_PER_SAMPLE
        return if (remainder == 0) {
            data
        } else {
            data.copyOf(data.size - remainder)
        }
    }

    /**
     * Convert ByteArray to ShortArray with proper little-endian byte order
     * This ensures correct PCM16 interpretation (same as web frontend's Int16Array)
     */
    private fun convertToShortArray(data: ByteArray): ShortArray {
        if (data.isEmpty()) {
            return ShortArray(0)
        }
        val shortCount = data.size / BYTES_PER_SAMPLE
        val shortArray = ShortArray(shortCount)

        // Use ByteBuffer with LITTLE_ENDIAN order (same as JavaScript Int16Array)
        val byteBuffer = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN)
        for (i in 0 until shortCount) {
            shortArray[i] = byteBuffer.getShort()
        }
        return shortArray
    }

    private fun ensureTrack(sampleRate: Int) {
        val desiredRate = sampleRate.takeIf { it > 0 } ?: OUTPUT_SAMPLE_RATE
        synchronized(audioLock) {
            val current = audioTrack
            if (current != null && currentSampleRate == desiredRate && current.state == AudioTrack.STATE_INITIALIZED) {
                return
            }
            current?.release()
            currentSampleRate = desiredRate
            audioTrack = createAudioTrack(desiredRate)
        }
    }

    private fun createAudioTrack(sampleRate: Int): AudioTrack {
        val minBuffer = AudioTrack.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        // Use larger buffer to prevent underrun and noise
        // At least 0.5 seconds of audio or 4x minBuffer
        val halfSecondBuffer = sampleRate * BYTES_PER_SAMPLE / 2
        val bufferSize = if (minBuffer > 0) {
            maxOf(minBuffer * 4, halfSecondBuffer)
        } else {
            halfSecondBuffer
        }

        val attributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
            .build()

        val format = AudioFormat.Builder()
            .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
            .setSampleRate(sampleRate)
            .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
            .build()

        return AudioTrack.Builder()
            .setAudioAttributes(attributes)
            .setAudioFormat(format)
            .setBufferSizeInBytes(bufferSize)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
    }
}
