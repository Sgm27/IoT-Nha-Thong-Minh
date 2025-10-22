package com.example.iot_nha_thong_minh.ui.chat

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.math.max

private const val DEFAULT_SAMPLE_RATE = 16_000
private const val DEFAULT_CHUNK_DURATION_MS = 100
private const val BYTES_PER_SAMPLE = 2

class GeminiAudioRecorder(
    val sampleRate: Int = DEFAULT_SAMPLE_RATE,
    val chunkDurationMillis: Int = DEFAULT_CHUNK_DURATION_MS,
    private val audioSource: Int = MediaRecorder.AudioSource.VOICE_RECOGNITION,
) {
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT
    private val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
    private val chunkSizeInBytes = max(BYTES_PER_SAMPLE * sampleRate * chunkDurationMillis / 1000, BYTES_PER_SAMPLE)
    private val bufferSizeInBytes = if (minBufferSize > 0) {
        max(minBufferSize, chunkSizeInBytes * 2)
    } else {
        minBufferSize
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var audioRecord: AudioRecord? = null
    private var recordingJob: Job? = null

    val isSupported: Boolean
        get() = minBufferSize > 0

    fun start(onChunk: (ByteArray) -> Unit, onError: (String) -> Unit): Boolean {
        if (recordingJob != null) {
            return true
        }
        if (!isSupported) {
            onError("Thiết bị của bạn không hỗ trợ ghi âm realtime cho Gemini.")
            return false
        }

        val recorder = try {
            AudioRecord(audioSource, sampleRate, channelConfig, audioFormat, bufferSizeInBytes)
        } catch (error: Exception) {
            Log.e("GeminiAudioRecorder", "Không thể tạo AudioRecord", error)
            onError("Không thể khởi động micro. Vui lòng thử lại.")
            return false
        }

        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            onError("Không thể khởi động micro. Vui lòng thử lại.")
            return false
        }

        return try {
            recorder.startRecording()
            audioRecord = recorder
            val job = scope.launch {
                val buffer = ByteArray(chunkSizeInBytes)
                var offset = 0
                try {
                    while (isActive) {
                        val bytesToRead = buffer.size - offset
                        if (bytesToRead <= 0) {
                            offset = 0
                            continue
                        }
                        val read = try {
                            recorder.read(buffer, offset, bytesToRead)
                        } catch (error: Exception) {
                            Log.e("GeminiAudioRecorder", "Lỗi khi đọc dữ liệu âm thanh", error)
                            -1
                        }
                        if (read > 0) {
                            offset += read
                            if (offset >= chunkSizeInBytes) {
                                val chunk = buffer.copyOf(offset)
                                try {
                                    onChunk(chunk)
                                } catch (error: Exception) {
                                    Log.e("GeminiAudioRecorder", "Không thể xử lý chunk âm thanh", error)
                                }
                                offset = 0
                            }
                        } else if (read == 0) {
                            // no-op, try reading again
                        } else {
                            Log.e("GeminiAudioRecorder", "Đọc âm thanh trả về lỗi: $read")
                            onError("Không thể ghi âm từ micro.")
                            break
                        }
                    }
                } finally {
                    if (offset > 0) {
                        val chunk = buffer.copyOf(offset)
                        try {
                            onChunk(chunk)
                        } catch (error: Exception) {
                            Log.e("GeminiAudioRecorder", "Không thể xử lý chunk âm thanh cuối", error)
                        }
                    }
                    cleanupRecorder(recorder)
                    if (audioRecord === recorder) {
                        audioRecord = null
                    }
                }
            }
            job.invokeOnCompletion {
                if (recordingJob === job) {
                    recordingJob = null
                }
            }
            recordingJob = job
            true
        } catch (error: IllegalStateException) {
            Log.e("GeminiAudioRecorder", "Không thể bắt đầu ghi âm", error)
            recorder.release()
            onError("Không thể khởi động micro. Vui lòng thử lại.")
            false
        }
    }

    fun stop() {
        val recorder = audioRecord
        audioRecord = null
        try {
            recorder?.stop()
        } catch (error: Exception) {
            Log.w("GeminiAudioRecorder", "Không thể dừng AudioRecord đúng cách", error)
        }
        recordingJob?.cancel()
        recordingJob = null
    }

    fun release() {
        stop()
        scope.cancel()
    }

    private fun cleanupRecorder(recorder: AudioRecord) {
        try {
            if (recorder.recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                recorder.stop()
            }
        } catch (error: Exception) {
            Log.w("GeminiAudioRecorder", "Không thể dừng AudioRecord", error)
        }
        try {
            recorder.release()
        } catch (error: Exception) {
            Log.w("GeminiAudioRecorder", "Không thể giải phóng AudioRecord", error)
        }
    }
}
