import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type KeyboardEvent
} from "react";

import {
  CAMERA_FRAME_INTERVAL_MS,
  CAMERA_IMAGE_MIME_TYPE,
  CAMERA_IMAGE_QUALITY,
  CAMERA_MAX_DIMENSION,
  INPUT_SAMPLE_RATE,
  MAX_IMAGE_SIZE_BYTES,
  OUTPUT_SAMPLE_RATE,
  PCM_CHUNK_DURATION_MS
} from "@/constants/gemini";
import { arrayBufferToBase64, base64ToArrayBuffer } from "@/lib/base64";
import { formatFileSize } from "@/lib/format";
import { concatFloat32, decodeAudioChunk, extractSampleRate, float32ToPCM16, resampleFloat32 } from "@/lib/audio";
import { createMessageId } from "@/lib/id";
import type { ChatMessage } from "@/types/chat";
import type { LightState } from "@/types/smart-home";

interface UseGeminiRealtimeOptions {
  showFeedback: (message: string, isError?: boolean) => void;
  onLightUpdate: (light: LightState) => void;
  beginMusicPlayback: (title: string, streamUrl: string) => Promise<boolean>;
  pauseCurrentMusic: () => boolean;
  resumeCurrentMusic: () => Promise<boolean>;
}

export const useGeminiRealtime = ({
  showFeedback,
  onLightUpdate,
  beginMusicPlayback,
  pauseCurrentMusic,
  resumeCurrentMusic
}: UseGeminiRealtimeOptions) => {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState<boolean>(false);
  const [geminiStatus, setGeminiStatus] = useState<string>("Đang kết nối tới Gemini...");
  const [isGeminiConnected, setIsGeminiConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isMicPermissionDenied, setIsMicPermissionDenied] = useState<boolean>(false);
  const [isCameraStreaming, setIsCameraStreaming] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraDimensions, setCameraDimensions] = useState<{ width: number; height: number } | null>(null);
  const [cameraCaptureIntervalMs, setCameraCaptureIntervalMs] = useState<number>(CAMERA_FRAME_INTERVAL_MS);

  const geminiSocketRef = useRef<WebSocket | null>(null);
  const geminiReconnectTimer = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<number>(0);
  const playbackQueueRef = useRef<Promise<void>>(Promise.resolve());
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const currentAssistantMessageIdRef = useRef<string | null>(null);
  const recordingStreamRef = useRef<MediaStream | null>(null);
  const recordingAudioContextRef = useRef<AudioContext | null>(null);
  const recordingProcessorRef = useRef<AudioWorkletNode | null>(null);
  const recordingSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const recordingGainNodeRef = useRef<GainNode | null>(null);
  const pendingInputSamplesRef = useRef<Float32Array | null>(null);
  const recordingWorkletContextRef = useRef<AudioContext | null>(null);
  const cameraVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const cameraCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const cameraCaptureTimerRef = useRef<number | null>(null);
  const cameraSendingRef = useRef<boolean>(false);

  const updateCameraDimensions = useCallback(() => {
    const video = cameraVideoRef.current;
    if (!video) {
      return;
    }

    const { videoWidth, videoHeight } = video;
    if (!videoWidth || !videoHeight) {
      return;
    }

    const longestEdge = Math.max(videoWidth, videoHeight);
    const scale = longestEdge > CAMERA_MAX_DIMENSION ? CAMERA_MAX_DIMENSION / longestEdge : 1;
    const targetWidth = Math.max(1, Math.round(videoWidth * scale));
    const targetHeight = Math.max(1, Math.round(videoHeight * scale));

    setCameraDimensions((previous) => {
      if (previous?.width === targetWidth && previous?.height === targetHeight) {
        return previous;
      }
      return { width: targetWidth, height: targetHeight };
    });
  }, [setCameraDimensions]);

  const clearSelectedImage = useCallback(() => {
    setSelectedImage(null);
    setSelectedImagePreview((previous) => {
      if (previous?.startsWith("blob:")) {
        URL.revokeObjectURL(previous);
      }
      return null;
    });
    if (imageInputRef.current) {
      imageInputRef.current.value = "";
    }
  }, []);

  const ensureAudioContext = useCallback(() => {
    if (typeof window === "undefined") {
      return null;
    }
    if (!audioContextRef.current) {
      const AudioContextConstructor = (window.AudioContext || (window as typeof window & {
        webkitAudioContext?: typeof AudioContext;
      }).webkitAudioContext) as typeof AudioContext | undefined;
      if (!AudioContextConstructor) {
        return null;
      }
      audioContextRef.current = new AudioContextConstructor({ sampleRate: OUTPUT_SAMPLE_RATE });
      audioQueueRef.current = 0;
      playbackQueueRef.current = Promise.resolve();
    }
    const context = audioContextRef.current;
    if (context.state === "suspended") {
      void context.resume();
    }
    return context;
  }, []);

  const processAssistantAudio = useCallback(
    async (audioPayload: string | { data?: string; mime_type?: string; sample_rate?: number }) => {
      const context = ensureAudioContext();
      if (!context) {
        return;
      }

      try {
        const payloadObject =
          typeof audioPayload === "string"
            ? { data: audioPayload }
            : audioPayload || {};

        const base64 = typeof payloadObject.data === "string" ? payloadObject.data : null;
        if (!base64) {
          return;
        }

        const parsedSampleRate =
          extractSampleRate(
            typeof payloadObject.mime_type === "string" ? payloadObject.mime_type : undefined,
            typeof payloadObject.sample_rate === "number" ? payloadObject.sample_rate : undefined
          ) || OUTPUT_SAMPLE_RATE;

        const arrayBuffer = base64ToArrayBuffer(base64);
        if (!arrayBuffer) {
          return;
        }

        const audioBuffer = await decodeAudioChunk(
          arrayBuffer,
          context,
          parsedSampleRate,
          typeof payloadObject.mime_type === "string" ? payloadObject.mime_type : undefined
        );
        if (!audioBuffer) {
          return;
        }

        const source = context.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(context.destination);

        const startTime = Math.max(context.currentTime, audioQueueRef.current);
        source.start(startTime);
        audioQueueRef.current = startTime + audioBuffer.duration;
      } catch (error) {
        console.error("Không thể phát âm thanh từ Gemini", error);
      }
    },
    [ensureAudioContext]
  );

  const playAssistantAudio = useCallback(
    (audioPayload: string | { data?: string; mime_type?: string; sample_rate?: number }) => {
      playbackQueueRef.current = playbackQueueRef.current
        .catch(() => undefined)
        .then(() => processAssistantAudio(audioPayload));
    },
    [processAssistantAudio]
  );

  const appendChatMessage = useCallback((message: Omit<ChatMessage, "id" | "timestamp"> & { id?: string }) => {
    setChatMessages((previous) => [
      ...previous,
      {
        id: message.id ?? createMessageId(),
        role: message.role,
        content: message.content ?? "",
        streaming: message.streaming,
        imageDataUrl: message.imageDataUrl,
        timestamp: Date.now()
      }
    ]);
  }, []);

  const updateAssistantMessage = useCallback(
    (text: string, finished: boolean) => {
      if (!text) {
        if (finished && currentAssistantMessageIdRef.current) {
          const messageId = currentAssistantMessageIdRef.current;
          setChatMessages((previous) =>
            previous.map((item) =>
              item.id === messageId
                ? { ...item, streaming: false, timestamp: Date.now() }
                : item
            )
          );
          currentAssistantMessageIdRef.current = null;
        }
        return;
      }

      setChatMessages((previous) => {
        let targetId = currentAssistantMessageIdRef.current;
        const existing = targetId ? previous.find((item) => item.id === targetId) : undefined;

        if (!existing) {
          targetId = createMessageId();
          currentAssistantMessageIdRef.current = targetId;
          return [
            ...previous,
            {
              id: targetId,
              role: "assistant",
              content: text,
              streaming: !finished,
              timestamp: Date.now()
            }
          ];
        }

        const previousContent = existing.content;
        const mergedContent = !finished && previousContent && text.startsWith(previousContent)
          ? text
          : finished
            ? text
            : `${previousContent}${text}`;

        const updated = previous.map((item) =>
          item.id === targetId
            ? {
                ...item,
                content: mergedContent,
                streaming: !finished,
                timestamp: finished ? Date.now() : item.timestamp
              }
            : item
        );

        if (finished) {
          currentAssistantMessageIdRef.current = null;
        }

        return updated;
      });
    },
    []
  );

  const handleGeminiPayload = useCallback(
    (payload: unknown) => {
      if (!payload || typeof payload !== "object") {
        return;
      }

      const data = payload as Record<string, unknown>;

      if ("setupComplete" in data) {
        const setupPayload = data.setupComplete;
        if (setupPayload && typeof setupPayload === "object") {
          const setupRecord = setupPayload as Record<string, unknown>;
          const rawMs = setupRecord.cameraCaptureIntervalMs;
          const rawSeconds = setupRecord.cameraCaptureIntervalSeconds;

          const parsedMs =
            typeof rawMs === "number" && Number.isFinite(rawMs) && rawMs > 0
              ? rawMs
              : typeof rawSeconds === "number" && Number.isFinite(rawSeconds) && rawSeconds > 0
                ? rawSeconds * 1000
                : undefined;

          if (parsedMs !== undefined) {
            const normalizedMs = Math.max(100, Math.round(parsedMs));
            setCameraCaptureIntervalMs(normalizedMs);
          }
        }

        setGeminiStatus("Đã kết nối với Gemini. Bạn có thể trò chuyện ngay!");
        return;
      }

      if ("type" in data && typeof data.type === "string") {
        switch (data.type) {
          case "keepalive": {
            if (geminiSocketRef.current && geminiSocketRef.current.readyState === WebSocket.OPEN) {
              geminiSocketRef.current.send(
                JSON.stringify({ keepalive: { timestamp: new Date().toISOString() } })
              );
            }
            return;
          }
          case "connection_error": {
            const message =
              typeof data.message === "string"
                ? data.message
                : "Không thể kết nối tới Gemini. Ứng dụng đang chuyển sang chế độ ngoại tuyến.";
            setIsGeminiConnected(false);
            setGeminiStatus(message);
            appendChatMessage({
              role: "system",
              content: message
            });
            showFeedback(message, true);
            return;
          }
          case "tool_call": {
            const functionName = typeof data.function_name === "string" ? data.function_name : "unknown";
            appendChatMessage({
              role: "system",
              content: `Gemini đang gọi chức năng “${functionName}”.`
            });
            return;
          }
          case "screen_navigation": {
            const action = typeof data.action === "string" ? data.action : "navigation";
            appendChatMessage({
              role: "system",
              content: `Ứng dụng đang thực hiện thao tác: ${action}`
            });
            return;
          }
          case "memory_update": {
            appendChatMessage({
              role: "system",
              content: "Gemini đã ghi nhớ thông tin mới về bạn."
            });
            return;
          }
          case "smart_home_light_update": {
            const location = typeof data.location === "string" ? data.location : "";
            const isOn = Boolean(data.is_on);
            if (location) {
              appendChatMessage({
                role: "system",
                content: `Đèn tại “${location}” hiện đang ${isOn ? "bật" : "tắt"}.`
              });
              onLightUpdate({ location, is_on: isOn });
            }
            return;
          }
          case "smart_home_music": {
            const matched = typeof data.matched_song === "string" ? data.matched_song : null;
            const requested = typeof data.requested_title === "string" ? data.requested_title : "bài hát";
            const streamUrl = typeof data.stream_url === "string" ? data.stream_url : null;
            appendChatMessage({
              role: "system",
              content: matched
                ? `Đang phát bài hát “${matched}” theo yêu cầu “${requested}”.`
                : `Không tìm thấy bài hát phù hợp với yêu cầu “${requested}”.`
            });
            if (matched && streamUrl) {
              void beginMusicPlayback(matched, streamUrl).then((started) => {
                if (started) {
                  showFeedback(`Đang phát bài: ${matched}`);
                } else {
                  showFeedback(
                    "Trình duyệt đang chặn phát nhạc tự động. Nhấp vào màn hình để bắt đầu phát.",
                    true
                  );
                }
              });
            } else if (matched && !streamUrl) {
              showFeedback(
                `Không thể chuẩn bị luồng phát cho bài hát “${matched}”. Vui lòng thử lại.`,
                true
              );
            } else if (!matched) {
              showFeedback(`Không tìm thấy bài hát phù hợp với yêu cầu “${requested}”.`, true);
            }
            return;
          }
          case "smart_home_music_control": {
            const action = typeof data.action === "string" ? data.action : "";
            const status = typeof data.status === "string" ? data.status : "";
            const matched = typeof data.matched_song === "string" ? data.matched_song : null;
            if (action === "pause") {
              if (status === "paused") {
                appendChatMessage({
                  role: "system",
                  content: matched ? `Đã tạm dừng bài hát “${matched}”.` : "Đã tạm dừng phát nhạc."
                });
                const paused = pauseCurrentMusic();
                if (paused) {
                  showFeedback(matched ? `Đã tạm dừng bài: ${matched}` : "Đã tạm dừng nhạc");
                } else {
                  showFeedback("Không thể tạm dừng nhạc trên trình duyệt.", true);
                }
              } else if (status === "no_active_song") {
                appendChatMessage({
                  role: "system",
                  content: "Không có bài hát nào đang phát để tạm dừng."
                });
                showFeedback("Không có bài hát nào đang phát.", true);
              }
              return;
            }
            if (action === "continue") {
              if (status === "playing") {
                appendChatMessage({
                  role: "system",
                  content: matched ? `Tiếp tục phát bài hát “${matched}”.` : "Tiếp tục phát nhạc."
                });
                void resumeCurrentMusic().then((resumed) => {
                  if (resumed) {
                    showFeedback(matched ? `Tiếp tục phát bài: ${matched}` : "Tiếp tục phát nhạc");
                  } else {
                    showFeedback("Không thể tiếp tục phát nhạc trên trình duyệt.", true);
                  }
                });
              } else if (status === "no_paused_song") {
                appendChatMessage({
                  role: "system",
                  content: "Không có bài hát nào đang tạm dừng để tiếp tục."
                });
                showFeedback("Không có bài hát nào đang tạm dừng.", true);
              }
              return;
            }
            return;
          }
          default:
            return;
        }
      }

      if ("transcription" in data && data.transcription && typeof data.transcription === "object") {
        const transcription = data.transcription as Record<string, unknown>;
        const text = typeof transcription.text === "string" ? transcription.text : "";
        const sender = typeof transcription.sender === "string" ? transcription.sender : "";
        const finished = Boolean(transcription.finished);

        if (sender === "Gemini") {
          updateAssistantMessage(text, finished);
        }
        return;
      }

      if ("text" in data && typeof data.text === "string") {
        updateAssistantMessage(data.text, true);
        return;
      }

      if ("audio" in data) {
        const audioData = data.audio;
        if (typeof audioData === "string" || (audioData && typeof audioData === "object")) {
          playAssistantAudio(audioData as string | { data?: string; mime_type?: string; sample_rate?: number });
        }
        return;
      }
    },
    [
      appendChatMessage,
      beginMusicPlayback,
      onLightUpdate,
      pauseCurrentMusic,
      playAssistantAudio,
      resumeCurrentMusic,
      showFeedback,
      updateAssistantMessage
    ]
  );

  const captureAndSendCameraFrame = useCallback(async () => {
    if (cameraSendingRef.current) {
      return;
    }

    const socket = geminiSocketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    const video = cameraVideoRef.current;
    if (!video || !cameraStreamRef.current) {
      return;
    }

    const { videoWidth, videoHeight, readyState } = video;
    if (!videoWidth || !videoHeight || readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      return;
    }

    const canvas = cameraCanvasRef.current ?? document.createElement("canvas");
    cameraCanvasRef.current = canvas;

    const longestEdge = Math.max(videoWidth, videoHeight);
    const scale = longestEdge > CAMERA_MAX_DIMENSION ? CAMERA_MAX_DIMENSION / longestEdge : 1;
    const targetWidth = Math.max(1, Math.round(videoWidth * scale));
    const targetHeight = Math.max(1, Math.round(videoHeight * scale));

    if (canvas.width !== targetWidth) {
      canvas.width = targetWidth;
    }
    if (canvas.height !== targetHeight) {
      canvas.height = targetHeight;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    context.drawImage(video, 0, 0, targetWidth, targetHeight);

    cameraSendingRef.current = true;
    try {
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob((result) => resolve(result), CAMERA_IMAGE_MIME_TYPE, CAMERA_IMAGE_QUALITY)
      );
      if (!blob) {
        return;
      }

      if (blob.size > MAX_IMAGE_SIZE_BYTES) {
        console.warn("Camera frame skipped because it exceeds the size limit");
        return;
      }

      const buffer = await blob.arrayBuffer();
      const base64 = arrayBufferToBase64(buffer);
      const mimeType = blob.type || CAMERA_IMAGE_MIME_TYPE;

      socket.send(
        JSON.stringify({
          realtime_input: {
            media_chunks: [
              {
                mime_type: mimeType,
                data: base64
              }
            ]
          }
        })
      );
    } catch (error) {
      console.error("Không thể gửi khung hình từ camera tới Gemini", error);
    } finally {
      cameraSendingRef.current = false;
    }
  }, []);

  const stopCameraStream = useCallback(() => {
    if (cameraCaptureTimerRef.current) {
      window.clearInterval(cameraCaptureTimerRef.current);
      cameraCaptureTimerRef.current = null;
    }

    cameraSendingRef.current = false;

    const stream = cameraStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore stop errors
        }
      });
      cameraStreamRef.current = null;
    }

    const video = cameraVideoRef.current;
    if (video) {
      try {
        video.pause();
      } catch {
        // ignore pause errors
      }
      video.srcObject = null;
    }

    setIsCameraStreaming(false);
    setCameraDimensions(null);
  }, []);

  const startCameraStream = useCallback(async () => {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      const message = "Thiết bị không hỗ trợ camera.";
      setCameraError(message);
      showFeedback(message, true);
      return;
    }

    setCameraError(null);

    if (cameraCaptureTimerRef.current) {
      window.clearInterval(cameraCaptureTimerRef.current);
      cameraCaptureTimerRef.current = null;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: CAMERA_MAX_DIMENSION },
          height: { ideal: CAMERA_MAX_DIMENSION }
        },
        audio: false
      });

      cameraStreamRef.current = stream;

      const video = cameraVideoRef.current;
      if (video) {
        video.srcObject = stream;
        video.playsInline = true;
        video.muted = true;
        const playPromise = video.play();
        if (playPromise) {
          void playPromise.catch(() => undefined);
        }
      }

      setIsCameraStreaming(true);
      updateCameraDimensions();
    } catch (error) {
      console.error("Không thể bật camera", error);

      if (error instanceof DOMException && error.name === "NotAllowedError") {
        const message = "Truy cập camera bị từ chối. Vui lòng kiểm tra quyền của trình duyệt.";
        setCameraError(message);
        showFeedback(message, true);
      } else {
        const message = "Không thể bật camera. Vui lòng thử lại.";
        setCameraError(message);
        showFeedback(message, true);
      }

      stopCameraStream();
    }
  }, [captureAndSendCameraFrame, showFeedback, stopCameraStream, updateCameraDimensions]);

  const toggleCameraStream = useCallback(() => {
    if (isCameraStreaming) {
      stopCameraStream();
    } else {
      void startCameraStream();
    }
  }, [isCameraStreaming, startCameraStream, stopCameraStream]);

  useEffect(() => {
    if (!isCameraStreaming) {
      return;
    }

    if (cameraCaptureTimerRef.current) {
      window.clearInterval(cameraCaptureTimerRef.current);
    }

    cameraCaptureTimerRef.current = window.setInterval(() => {
      void captureAndSendCameraFrame();
    }, cameraCaptureIntervalMs);

    return () => {
      if (cameraCaptureTimerRef.current) {
        window.clearInterval(cameraCaptureTimerRef.current);
        cameraCaptureTimerRef.current = null;
      }
    };
  }, [cameraCaptureIntervalMs, captureAndSendCameraFrame, isCameraStreaming]);

  const handleImageSelect = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) {
        clearSelectedImage();
        return;
      }

      if (!file.type || !file.type.startsWith("image/")) {
        showFeedback("Chỉ hỗ trợ gửi tệp hình ảnh.", true);
        clearSelectedImage();
        return;
      }

      if (file.size > MAX_IMAGE_SIZE_BYTES) {
        showFeedback(
          `Ảnh vượt quá giới hạn ${formatFileSize(MAX_IMAGE_SIZE_BYTES)}. Vui lòng chọn ảnh khác.`,
          true
        );
        clearSelectedImage();
        return;
      }

      setSelectedImage(file);
      setSelectedImagePreview((previous) => {
        if (previous?.startsWith("blob:")) {
          URL.revokeObjectURL(previous);
        }
        return URL.createObjectURL(file);
      });
    },
    [clearSelectedImage, showFeedback]
  );

  const sendSelectedImage = useCallback(async () => {
    if (isUploadingImage) {
      return;
    }

    const file = selectedImage;
    if (!file) {
      showFeedback("Vui lòng chọn một ảnh trước khi gửi.", true);
      return;
    }

    const socket = geminiSocketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      showFeedback("Kết nối với Gemini chưa sẵn sàng", true);
      return;
    }

    setIsUploadingImage(true);
    try {
      const buffer = await file.arrayBuffer();
      const base64 = arrayBufferToBase64(buffer);
      const mimeType = file.type || "image/png";
      socket.send(
        JSON.stringify({
          realtime_input: {
            media_chunks: [
              {
                mime_type: mimeType,
                data: base64
              }
            ]
          }
        })
      );

      const dataUrl = `data:${mimeType};base64,${base64}`;
      appendChatMessage({
        role: "user",
        content: file.name ? `Đã gửi ảnh ${file.name}` : "Đã gửi một ảnh",
        imageDataUrl: dataUrl
      });
      showFeedback("Đã gửi ảnh tới Gemini");
      clearSelectedImage();
    } catch (error) {
      console.error("Không thể gửi ảnh tới Gemini", error);
      showFeedback("Không thể gửi ảnh. Vui lòng thử lại.", true);
    } finally {
      setIsUploadingImage(false);
    }
  }, [appendChatMessage, clearSelectedImage, isUploadingImage, selectedImage, showFeedback]);

  const sendChatMessage = useCallback(() => {
    const message = chatInput.trim();
    if (!message) {
      showFeedback("Vui lòng nhập nội dung tin nhắn", true);
      return;
    }

    const socket = geminiSocketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      showFeedback("Kết nối với Gemini chưa sẵn sàng", true);
      return;
    }

    appendChatMessage({ role: "user", content: message });
    socket.send(JSON.stringify({ text: message }));
    setChatInput("");
  }, [appendChatMessage, chatInput, showFeedback]);

  const handleChatSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      sendChatMessage();
    },
    [sendChatMessage]
  );

  const handleChatKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
      }
    },
    [sendChatMessage]
  );

  const stopRecording = useCallback(() => {
    const processor = recordingProcessorRef.current;
    if (processor) {
      processor.disconnect();
      processor.port.onmessage = null;
      try {
        processor.port.close();
      } catch {
        // Ignore closing errors
      }
      recordingProcessorRef.current = null;
    }

    const source = recordingSourceRef.current;
    if (source) {
      source.disconnect();
      recordingSourceRef.current = null;
    }

    const gainNode = recordingGainNodeRef.current;
    if (gainNode) {
      gainNode.disconnect();
      recordingGainNodeRef.current = null;
    }

    const context = recordingAudioContextRef.current;
    if (context) {
      context.close().catch(() => undefined);
      recordingAudioContextRef.current = null;
      if (recordingWorkletContextRef.current === context) {
        recordingWorkletContextRef.current = null;
      }
    }

    pendingInputSamplesRef.current = null;

    const stream = recordingStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      recordingStreamRef.current = null;
    }

    setIsRecording(false);
  }, []);

  const startRecording = useCallback(async () => {
    if (isRecording) {
      return;
    }
    setRecordingError(null);

    const socket = geminiSocketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      showFeedback("Kết nối với Gemini chưa sẵn sàng", true);
      return;
    }

    if (typeof navigator === "undefined") {
      setRecordingError("Không thể truy cập micro trong môi trường hiện tại.");
      return;
    }

    const { mediaDevices } = navigator;
    if (!mediaDevices?.getUserMedia) {
      setRecordingError("Không thể truy cập micro trên thiết bị này.");
      return;
    }

    try {
      const stream = await mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: INPUT_SAMPLE_RATE,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      setIsMicPermissionDenied(false);
      recordingStreamRef.current = stream;

      const AudioContextConstructor = (window.AudioContext || (window as typeof window & {
        webkitAudioContext?: typeof AudioContext;
      }).webkitAudioContext) as typeof AudioContext | undefined;

      if (!AudioContextConstructor) {
        setRecordingError("Trình duyệt không hỗ trợ Web Audio API.");
        stopRecording();
        return;
      }

      const recordingContext = new AudioContextConstructor({ sampleRate: INPUT_SAMPLE_RATE });
      recordingAudioContextRef.current = recordingContext;
      pendingInputSamplesRef.current = null;

      if (recordingContext.state === "suspended") {
        await recordingContext.resume().catch(() => undefined);
      }

      const source = recordingContext.createMediaStreamSource(stream);
      recordingSourceRef.current = source;

      const gainNode = recordingContext.createGain();
      gainNode.gain.value = 0;
      recordingGainNodeRef.current = gainNode;

      const pcmChunkSize = Math.max(1, Math.floor((INPUT_SAMPLE_RATE * PCM_CHUNK_DURATION_MS) / 1000));
      const contextSampleRate = recordingContext.sampleRate;

      if (!("audioWorklet" in recordingContext)) {
        setRecordingError("Trình duyệt không hỗ trợ AudioWorklet.");
        stopRecording();
        return;
      }

      if (recordingWorkletContextRef.current !== recordingContext) {
        try {
          await recordingContext.audioWorklet.addModule(
            new URL("../worklets/pcm-worklet-processor.js", import.meta.url)
          );
          recordingWorkletContextRef.current = recordingContext;
        } catch (error) {
          console.error("Không thể tải audio worklet", error);
          setRecordingError("Không thể khởi động micro. Vui lòng thử lại.");
          stopRecording();
          return;
        }
      }

      const processor = new AudioWorkletNode(recordingContext, "pcm-worklet-processor", {
        numberOfInputs: 1,
        numberOfOutputs: 1,
        outputChannelCount: [1]
      });
      recordingProcessorRef.current = processor;

      processor.port.onmessage = (event) => {
        const channelData = event.data as Float32Array | null;
        if (!(channelData instanceof Float32Array) || channelData.length === 0) {
          return;
        }

        const resampled = resampleFloat32(channelData, contextSampleRate, INPUT_SAMPLE_RATE);
        const existing = pendingInputSamplesRef.current;
        let combined = concatFloat32(existing, resampled);

        while (combined.length >= pcmChunkSize) {
          const chunk = combined.slice(0, pcmChunkSize);
          combined = combined.slice(pcmChunkSize);

          const pcmBuffer = float32ToPCM16(chunk);
          const base64 = arrayBufferToBase64(pcmBuffer);
          const activeSocket = geminiSocketRef.current;
          if (activeSocket && activeSocket.readyState === WebSocket.OPEN) {
            activeSocket.send(
              JSON.stringify({
                realtime_input: {
                  media_chunks: [
                    {
                      mime_type: `audio/pcm;rate=${INPUT_SAMPLE_RATE}`,
                      data: base64
                    }
                  ]
                }
              })
            );
          }
        }

        pendingInputSamplesRef.current = combined.length > 0 ? combined : null;
      };

      source.connect(processor);
      processor.connect(gainNode);
      gainNode.connect(recordingContext.destination);

      setIsRecording(true);
    } catch (error) {
      console.error("Không thể khởi động micro", error);
      stopRecording();
      if (error instanceof DOMException && error.name === "NotAllowedError") {
        setIsMicPermissionDenied(true);
        setRecordingError("Truy cập micro đã bị từ chối. Hãy cấp quyền và thử lại.");
      } else {
        setRecordingError("Không thể khởi động micro. Vui lòng thử lại.");
      }
    }
  }, [isRecording, showFeedback, stopRecording]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
      return;
    }
    void startRecording();
  }, [isRecording, startRecording, stopRecording]);

  useEffect(() => {
    const video = cameraVideoRef.current;
    if (!video) {
      return;
    }

    const handleMetadata = () => {
      updateCameraDimensions();
    };

    video.addEventListener("loadedmetadata", handleMetadata);
    video.addEventListener("resize", handleMetadata);
    handleMetadata();

    return () => {
      video.removeEventListener("loadedmetadata", handleMetadata);
      video.removeEventListener("resize", handleMetadata);
    };
  }, [updateCameraDimensions]);

  useEffect(() => {
    if (!isGeminiConnected && isCameraStreaming) {
      const message = "Mất kết nối với Gemini. Camera đã tắt.";
      setCameraError(message);
      showFeedback(message, true);
      stopCameraStream();
    }
  }, [isCameraStreaming, isGeminiConnected, showFeedback, stopCameraStream]);

  useEffect(() => {
    if (!isGeminiConnected && isRecording) {
      stopRecording();
    }
  }, [isGeminiConnected, isRecording, stopRecording]);

  useEffect(() => {
    return () => {
      if (selectedImagePreview?.startsWith("blob:")) {
        URL.revokeObjectURL(selectedImagePreview);
      }
    };
  }, [selectedImagePreview]);

  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, [stopCameraStream]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) {
      return;
    }
    container.scrollTop = container.scrollHeight;
  }, [chatMessages]);

  useEffect(() => {
    let isMounted = true;

    const connectGemini = () => {
      if (!isMounted || geminiSocketRef.current) {
        return;
      }

      try {
        setGeminiStatus("Đang kết nối tới Gemini...");
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(`${protocol}://${window.location.host}/ws/gemini`);
        geminiSocketRef.current = socket;

        socket.addEventListener("open", () => {
          if (!isMounted) {
            return;
          }
          setIsGeminiConnected(true);
          setGeminiStatus("Đã kết nối với Gemini. Bạn có thể trò chuyện ngay!");
        });

        socket.addEventListener("message", (event) => {
          try {
            const payload = JSON.parse(event.data);
            handleGeminiPayload(payload);
          } catch (error) {
            console.error("Không thể phân tích dữ liệu Gemini", error);
          }
        });

        socket.addEventListener("close", () => {
          if (geminiSocketRef.current === socket) {
            geminiSocketRef.current = null;
          }
          if (isMounted) {
            setIsGeminiConnected(false);
            setGeminiStatus("Mất kết nối tới Gemini. Đang thử kết nối lại...");
            geminiReconnectTimer.current = window.setTimeout(connectGemini, 3000);
          }
        });

        socket.addEventListener("error", () => {
          socket.close();
        });
      } catch (error) {
        console.error("Không thể kết nối Gemini", error);
        if (isMounted) {
          setIsGeminiConnected(false);
          setGeminiStatus("Không thể kết nối Gemini. Thử lại sau.");
          geminiReconnectTimer.current = window.setTimeout(connectGemini, 3000);
        }
      }
    };

    connectGemini();

    return () => {
      isMounted = false;
      if (geminiReconnectTimer.current) {
        window.clearTimeout(geminiReconnectTimer.current);
        geminiReconnectTimer.current = null;
      }
      geminiSocketRef.current?.close();
      geminiSocketRef.current = null;
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => undefined);
        audioContextRef.current = null;
        audioQueueRef.current = 0;
        playbackQueueRef.current = Promise.resolve();
      }
    };
  }, [handleGeminiPayload]);

  useEffect(() => () => {
    stopRecording();
  }, [stopRecording]);

  return {
    geminiStatus,
    isGeminiConnected,
    chatMessages,
    chatInput,
    setChatInput,
    handleChatSubmit,
    handleChatKeyDown,
    sendChatMessage,
    selectedImage,
    selectedImagePreview,
    handleImageSelect,
    clearSelectedImage,
    sendSelectedImage,
    isUploadingImage,
    isRecording,
    toggleRecording,
    recordingError,
    isMicPermissionDenied,
    chatContainerRef,
    imageInputRef,
    cameraVideoRef,
    isCameraStreaming,
    toggleCameraStream,
    cameraError,
    cameraDimensions
  };
};

export const GEMINI_MAX_IMAGE_SIZE = MAX_IMAGE_SIZE_BYTES;
