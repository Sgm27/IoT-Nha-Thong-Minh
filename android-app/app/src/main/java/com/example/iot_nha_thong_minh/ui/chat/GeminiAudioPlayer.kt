package com.example.iot_nha_thong_minh.ui.chat

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.util.Log
import com.example.iot_nha_thong_minh.data.remote.GeminiRealtimeAudio
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch

private const val DEFAULT_SAMPLE_RATE = 24_000

class GeminiAudioPlayer {
    private data class AudioChunk(val data: ByteArray, val sampleRate: Int)

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val queue = Channel<AudioChunk>(capacity = Channel.UNLIMITED)
    private val audioLock = Any()

    @Volatile
    private var audioTrack: AudioTrack? = null

    @Volatile
    private var currentSampleRate = DEFAULT_SAMPLE_RATE

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
        val rate = audio.sampleRate?.takeIf { it > 0 } ?: currentSampleRate
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

    private fun playChunk(chunk: AudioChunk) {
        try {
            ensureTrack(chunk.sampleRate)
            val track = audioTrack ?: return
            var offset = 0
            val bytes = chunk.data
            while (offset < bytes.size) {
                val written = synchronized(audioLock) {
                    try {
                        track.write(bytes, offset, bytes.size - offset)
                    } catch (error: IllegalStateException) {
                        Log.e("GeminiAudioPlayer", "Không thể ghi dữ liệu âm thanh", error)
                        0
                    }
                }
                if (written <= 0) {
                    break
                }
                offset += written
            }
            synchronized(audioLock) {
                if (track.playState != AudioTrack.PLAYSTATE_PLAYING) {
                    try {
                        track.play()
                    } catch (error: IllegalStateException) {
                        Log.e("GeminiAudioPlayer", "Không thể phát âm thanh", error)
                    }
                }
            }
        } catch (error: Exception) {
            Log.e("GeminiAudioPlayer", "Lỗi khi phát âm thanh của Gemini", error)
        }
    }

    private fun ensureTrack(sampleRate: Int) {
        val desiredRate = sampleRate.takeIf { it > 0 } ?: DEFAULT_SAMPLE_RATE
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
        val bufferSize = if (minBuffer > 0) minBuffer else sampleRate
        val attributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
            .setLegacyStreamType(AudioManager.STREAM_MUSIC)
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
