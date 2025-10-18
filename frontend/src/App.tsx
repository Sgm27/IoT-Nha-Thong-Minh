import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent
} from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface LightState {
  location: string;
  is_on: boolean;
}

interface FeedbackState {
  message: string;
  isError?: boolean;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  streaming?: boolean;
}

async function apiClient<TResponse>(url: string, options: RequestInit = {}): Promise<TResponse> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json"
    },
    ...options
  });

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const payload = await response.json();
      detail = payload?.detail;
    } catch (error) {
      detail = undefined;
    }
    const errorMessage = detail || response.statusText || "Đã xảy ra lỗi";
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return response.json();
}

const normalizeLocation = (location: string) => location.trim().toLowerCase();

const sortLights = (lights: LightState[]) =>
  [...lights].sort((a, b) => a.location.localeCompare(b.location, "vi", { sensitivity: "base" }));

const INPUT_SAMPLE_RATE = 16000; // Sample rate expected by Gemini Live for incoming audio
const OUTPUT_SAMPLE_RATE = 24000; // Sample rate returned by Gemini Live when synthesising speech
const PCM_CHUNK_DURATION_MS = 100; // Chunk microphone audio in ~100ms windows for streaming

const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
};

const createMessageId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const concatFloat32 = (existing: Float32Array | null, incoming: Float32Array) => {
  if (!existing || existing.length === 0) {
    return incoming.slice();
  }
  if (!incoming || incoming.length === 0) {
    return existing.slice();
  }
  const result = new Float32Array(existing.length + incoming.length);
  result.set(existing, 0);
  result.set(incoming, existing.length);
  return result;
};

const resampleFloat32 = (input: Float32Array, sourceRate: number, targetRate: number) => {
  if (sourceRate === targetRate || input.length === 0) {
    return input.slice();
  }
  const sampleCount = Math.max(1, Math.round((input.length * targetRate) / sourceRate));
  const result = new Float32Array(sampleCount);
  const ratio = sourceRate / targetRate;

  for (let index = 0; index < sampleCount; index += 1) {
    const position = index * ratio;
    const leftIndex = Math.floor(position);
    const rightIndex = Math.min(leftIndex + 1, input.length - 1);
    const interpolation = position - leftIndex;
    const leftValue = input[leftIndex];
    const rightValue = input[rightIndex];
    result[index] = leftValue + (rightValue - leftValue) * interpolation;
  }

  return result;
};

const float32ToPCM16 = (input: Float32Array) => {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);
  for (let index = 0; index < input.length; index += 1) {
    const value = clamp(input[index], -1, 1);
    const intSample = value < 0 ? value * 0x8000 : value * 0x7fff;
    view.setInt16(index * 2, Math.round(intSample), true);
  }
  return buffer;
};

const extractSampleRate = (mimeType?: string, fallback?: number) => {
  if (typeof fallback === "number" && Number.isFinite(fallback) && fallback > 0) {
    return fallback;
  }
  if (!mimeType) {
    return undefined;
  }
  const match = /rate\s*=\s*(\d+)/i.exec(mimeType);
  if (!match) {
    return undefined;
  }
  const parsed = Number.parseInt(match[1], 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
};

export default function App() {
  const [lights, setLights] = useState<LightState[]>([]);
  const [musicLibrary, setMusicLibrary] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  const [lightLocation, setLightLocation] = useState<string>("");
  const [musicTitle, setMusicTitle] = useState<string>("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [geminiStatus, setGeminiStatus] = useState<string>("Đang kết nối tới Gemini...");
  const [isGeminiConnected, setIsGeminiConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isMicPermissionDenied, setIsMicPermissionDenied] = useState<boolean>(false);
  const reconnectTimer = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const geminiSocketRef = useRef<WebSocket | null>(null);
  const geminiReconnectTimer = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<number>(0);
  const playbackQueueRef = useRef<Promise<void>>(Promise.resolve());
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const currentAssistantMessageIdRef = useRef<string | null>(null);
  const recordingStreamRef = useRef<MediaStream | null>(null);
  const recordingAudioContextRef = useRef<AudioContext | null>(null);
  const recordingProcessorRef = useRef<AudioWorkletNode | null>(null);
  const recordingSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const recordingGainNodeRef = useRef<GainNode | null>(null);
  const pendingInputSamplesRef = useRef<Float32Array | null>(null);
  const recordingWorkletLoadedRef = useRef<boolean>(false);

  const showFeedback = useCallback((message: string, isError = false) => {
    setFeedback({ message, isError });
  }, []);

  const applyLightSnapshot = useCallback((snapshot: LightState[]) => {
    const validLights = snapshot
      .filter((light): light is LightState => Boolean(light && light.location))
      .map((light) => ({
        location: light.location,
        is_on: Boolean(light.is_on)
      }));
    const unique = new Map(validLights.map((light) => [normalizeLocation(light.location), light]));
    setLights(sortLights(Array.from(unique.values())));
  }, []);

  const applyLightUpdate = useCallback((light: LightState) => {
    if (!light?.location) return;
    setLights((previous) => {
      const map = new Map(previous.map((item) => [normalizeLocation(item.location), item]));
      map.set(normalizeLocation(light.location), {
        location: light.location,
        is_on: Boolean(light.is_on)
      });
      return sortLights(Array.from(map.values()));
    });
  }, []);

  const refreshLights = useCallback(async () => {
    try {
      const data = await apiClient<LightState[]>("/smart-home/lights");
      applyLightSnapshot(data);
    } catch (error) {
      if (error instanceof Error) {
        showFeedback(error.message, true);
      }
    }
  }, [applyLightSnapshot, showFeedback]);

  const refreshMusicLibrary = useCallback(async () => {
    try {
      const library = await apiClient<string[]>("/smart-home/music/library");
      setMusicLibrary(library);
    } catch (error) {
      if (error instanceof Error) {
        showFeedback(error.message, true);
      }
    }
  }, [showFeedback]);

  useEffect(() => {
    refreshLights();
    refreshMusicLibrary();
  }, [refreshLights, refreshMusicLibrary]);

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

        const parsedSampleRate = extractSampleRate(
          typeof payloadObject.mime_type === "string" ? payloadObject.mime_type : undefined,
          typeof payloadObject.sample_rate === "number" ? payloadObject.sample_rate : undefined
        ) || OUTPUT_SAMPLE_RATE;

        const binaryString = atob(base64);
        const buffer = new ArrayBuffer(binaryString.length);
        const bytes = new Uint8Array(buffer);
        for (let index = 0; index < binaryString.length; index += 1) {
          bytes[index] = binaryString.charCodeAt(index);
        }

        const dataView = new DataView(buffer);
        const sampleCount = Math.floor(binaryString.length / 2);
        const floatData = new Float32Array(sampleCount);
        for (let sampleIndex = 0; sampleIndex < sampleCount; sampleIndex += 1) {
          const sample = dataView.getInt16(sampleIndex * 2, true);
          floatData[sampleIndex] = sample / 32768;
        }

        const targetSampleRate = context.sampleRate;
        const processedData =
          targetSampleRate === parsedSampleRate
            ? floatData
            : resampleFloat32(floatData, parsedSampleRate, targetSampleRate);

        const audioBuffer = context.createBuffer(1, processedData.length, targetSampleRate);
        audioBuffer.copyToChannel(processedData, 0);

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
        content: message.content,
        streaming: message.streaming,
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
              applyLightUpdate({ location, is_on: isOn });
            }
            return;
          }
          case "smart_home_music": {
            const matched = typeof data.matched_song === "string" ? data.matched_song : null;
            const requested = typeof data.requested_title === "string" ? data.requested_title : "bài hát";
            appendChatMessage({
              role: "system",
              content: matched
                ? `Đang phát bài hát “${matched}” theo yêu cầu “${requested}”.`
                : `Không tìm thấy bài hát phù hợp với yêu cầu “${requested}”.`
            });
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
    [appendChatMessage, applyLightUpdate, playAssistantAudio, updateAssistantMessage]
  );

  useEffect(() => {
    let isMounted = true;

    const connect = () => {
      if (!isMounted || socketRef.current) {
        return;
      }
      try {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(`${protocol}://${window.location.host}/smart-home/lights/stream`);
        socketRef.current = socket;

        socket.addEventListener("message", (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload.type === "snapshot" && Array.isArray(payload.lights)) {
              applyLightSnapshot(payload.lights);
            } else if (payload.type === "update" && payload.light) {
              applyLightUpdate(payload.light);
            }
          } catch (error) {
            console.error("Không thể phân tích dữ liệu websocket", error);
          }
        });

        socket.addEventListener("close", () => {
          if (socketRef.current === socket) {
            socketRef.current = null;
            if (isMounted) {
              reconnectTimer.current = window.setTimeout(connect, 3000);
            }
          }
        });

        socket.addEventListener("error", () => {
          socket.close();
        });
      } catch (error) {
        console.error("Không thể kết nối websocket", error);
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [applyLightSnapshot, applyLightUpdate]);

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

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) {
      return;
    }
    container.scrollTop = container.scrollHeight;
  }, [chatMessages]);

  const handleLightAction = useCallback(
    async (action: "on" | "off") => {
      const location = lightLocation.trim();
      if (!location) {
        showFeedback("Vui lòng nhập vị trí đèn", true);
        return;
      }

      try {
        const endpoint = action === "on" ? "/smart-home/lights/on" : "/smart-home/lights/off";
        const result = await apiClient<LightState>(endpoint, {
          method: "POST",
          body: JSON.stringify({ location })
        });
        showFeedback(`Đèn tại "${result.location}" hiện đang ${result.is_on ? "bật" : "tắt"}.`);
        setLightLocation("");
        refreshLights();
      } catch (error) {
        if (error instanceof Error) {
          showFeedback(error.message, true);
        }
      }
    },
    [lightLocation, refreshLights, showFeedback]
  );

  const handleMusicSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const title = musicTitle.trim();
      if (!title) {
        showFeedback("Vui lòng nhập tên bài hát", true);
        return;
      }

      try {
        const response = await apiClient<{ selected_song: string }>("/smart-home/music/play", {
          method: "POST",
          body: JSON.stringify({ title })
        });
        showFeedback(`Đang phát bài: ${response.selected_song}`);
        setMusicTitle("");
      } catch (error) {
        if (error instanceof Error) {
          showFeedback(error.message, true);
        }
      }
    },
    [musicTitle, showFeedback]
  );

  const hasLights = lights.length > 0;
  const sortedLibrary = useMemo(
    () => [...musicLibrary].sort((a, b) => a.localeCompare(b, "vi", { sensitivity: "base" })),
    [musicLibrary]
  );

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
      } catch (error) {
        // Ignore closing errors – the port may already be closed.
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

      if (!recordingWorkletLoadedRef.current) {
        try {
          await recordingContext.audioWorklet.addModule(
            new URL("./worklets/pcm-worklet-processor.js", import.meta.url)
          );
          recordingWorkletLoadedRef.current = true;
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
    if (!isGeminiConnected && isRecording) {
      stopRecording();
    }
  }, [isGeminiConnected, isRecording, stopRecording]);

  useEffect(() => () => {
    stopRecording();
  }, [stopRecording]);

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="container flex flex-col gap-6 py-10">
        <header className="space-y-2 text-center">
          <h1 className="text-3xl font-bold sm:text-4xl">Điều khiển Nhà Thông Minh</h1>
          <p className="text-muted-foreground">
            Kiểm thử nhanh các chức năng đèn và phát nhạc của backend FastAPI.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Quản lý đèn</CardTitle>
              <CardDescription>
                Theo dõi trạng thái đèn và gửi lệnh bật/tắt tức thời.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-6">
              <form
                className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto] sm:items-end"
                onSubmit={(event) => event.preventDefault()}
              >
                <div className="space-y-2 sm:col-span-1">
                  <Label htmlFor="light-location">Vị trí đèn</Label>
                  <Input
                    id="light-location"
                    value={lightLocation}
                    onChange={(event) => setLightLocation(event.target.value)}
                    placeholder="Ví dụ: phòng khách"
                  />
                </div>
                <div className="flex flex-col gap-2 sm:col-span-1 sm:flex-row">
                  <Button type="button" className="flex-1" onClick={() => handleLightAction("on")}>
                    Bật đèn
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="flex-1"
                    onClick={() => handleLightAction("off")}
                  >
                    Tắt đèn
                  </Button>
                </div>
              </form>

              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Trạng thái các đèn</h3>
                <div className="overflow-hidden rounded-lg border bg-background">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-1/2">Vị trí</TableHead>
                        <TableHead>Trạng thái</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {hasLights ? (
                        lights.map((light) => (
                          <TableRow key={normalizeLocation(light.location)}>
                            <TableCell className="font-medium">{light.location}</TableCell>
                            <TableCell>{light.is_on ? "Bật" : "Tắt"}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={2} className="text-center text-muted-foreground">
                            Chưa có dữ liệu
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Phát nhạc</CardTitle>
              <CardDescription>Yêu cầu backend phát bài hát mong muốn.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-6">
              <form className="space-y-4" onSubmit={handleMusicSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="song-title">Tên bài hát</Label>
                  <Input
                    id="song-title"
                    value={musicTitle}
                    onChange={(event) => setMusicTitle(event.target.value)}
                    placeholder="Nhập tên bài hát muốn nghe"
                  />
                </div>
                <Button type="submit" className="w-full sm:w-auto">
                  Tìm và phát
                </Button>
              </form>

              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Thư viện hiện có</h3>
                <div className="rounded-lg border bg-background p-4">
                  {sortedLibrary.length ? (
                    <ul className="grid gap-2">
                      {sortedLibrary.map((song) => (
                        <li key={song} className="text-sm">
                          {song}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">Thư viện trống</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Trò chuyện với Gemini</CardTitle>
            <CardDescription>
              Gemini hỗ trợ giọng nói và văn bản nhờ cấu hình realtime của Gemini Live API.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col gap-4">
            <div className="flex items-center justify-between rounded-lg border bg-background px-4 py-2 text-sm text-muted-foreground">
              <span>Trạng thái: {geminiStatus}</span>
              <span
                className={cn(
                  "flex h-2 w-2 rounded-full",
                  isGeminiConnected ? "bg-green-500" : "bg-yellow-500 animate-pulse"
                )}
                aria-hidden
              />
            </div>
            <div className="flex flex-col gap-2 rounded-lg border bg-background px-4 py-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={isRecording ? "default" : "secondary"}
                    onClick={toggleRecording}
                    disabled={!isGeminiConnected}
                  >
                    {isRecording ? "Tắt micro" : "Bật micro"}
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    {isRecording
                      ? "Đang ghi âm và gửi tới Gemini"
                      : "Nhấn để trò chuyện với Gemini bằng giọng nói"}
                  </span>
                </div>
                {!isGeminiConnected ? (
                  <span className="text-xs text-muted-foreground">Cần kết nối Gemini để sử dụng micro</span>
                ) : null}
              </div>
              {isMicPermissionDenied ? (
                <p className="text-xs text-destructive">
                  Truy cập micro bị từ chối. Vui lòng kiểm tra quyền của trình duyệt.
                </p>
              ) : null}
              {recordingError ? (
                <p className="text-xs text-destructive">{recordingError}</p>
              ) : null}
            </div>
            <div className="flex-1 overflow-hidden rounded-lg border bg-background">
              <div ref={chatContainerRef} className="h-80 space-y-4 overflow-y-auto p-4 text-sm">
                {chatMessages.length ? (
                  chatMessages.map((message) => (
                    <div
                      key={message.id}
                      className={cn(
                        "flex flex-col gap-1",
                        message.role === "user" ? "items-end" : "items-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[85%] rounded-lg px-3 py-2",
                          message.role === "assistant"
                            ? "bg-primary/10 text-primary-foreground/90"
                            : message.role === "user"
                              ? "bg-muted text-foreground"
                              : "bg-amber-50 text-amber-900"
                        )}
                      >
                        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      </div>
                      {message.streaming ? (
                        <span className="text-xs text-muted-foreground">Gemini đang trả lời...</span>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <div className="flex h-full items-center justify-center text-center text-muted-foreground">
                    Chưa có cuộc trò chuyện nào. Hãy gửi lời chào cho Gemini nhé!
                  </div>
                )}
              </div>
            </div>
            <form className="flex flex-col gap-3" onSubmit={handleChatSubmit}>
              <label className="space-y-2">
                <span className="text-sm font-medium">Tin nhắn</span>
                <textarea
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  onKeyDown={handleChatKeyDown}
                  rows={3}
                  className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Nhập nội dung bạn muốn trao đổi với Gemini"
                />
              </label>
              <div className="flex justify-end gap-2">
                <Button type="submit" disabled={!isGeminiConnected}>
                  Gửi tin nhắn
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {feedback?.message && (
          <div
            className={cn(
              "rounded-lg border p-4 text-sm",
              feedback.isError
                ? "border-destructive/40 bg-destructive/10 text-destructive"
                : "border-primary/40 bg-primary/10 text-primary"
            )}
          >
            {feedback.message}
          </div>
        )}
      </div>
    </div>
  );
}
