import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { apiClient } from "@/lib/api-client";
import { toAbsoluteUrl } from "@/lib/url";
import type { MusicPlaybackResponse, MusicPlaybackState } from "@/types/smart-home";

interface UseMusicControllerOptions {
  showFeedback: (message: string, isError?: boolean) => void;
}

export const useMusicController = ({ showFeedback }: UseMusicControllerOptions) => {
  const [musicLibrary, setMusicLibrary] = useState<string[]>([]);
  const [currentSong, setCurrentSong] = useState<{ title: string; url: string } | null>(null);
  const [isMusicPaused, setIsMusicPaused] = useState<boolean>(false);
  const [musicState, setMusicState] = useState<MusicPlaybackState | null>(null);
  const [liveMusicPosition, setLiveMusicPosition] = useState<number>(0);
  const [musicTitle, setMusicTitle] = useState<string>("");
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const musicSocketRef = useRef<WebSocket | null>(null);
  const musicReconnectTimer = useRef<number | null>(null);
  const autoplayUnlockCleanupRef = useRef<(() => void) | null>(null);
  const isMusicControlFromServerRef = useRef<boolean>(false);

  const clearPendingAutoplayUnlock = useCallback(() => {
    const cleanup = autoplayUnlockCleanupRef.current;
    if (cleanup) {
      cleanup();
      autoplayUnlockCleanupRef.current = null;
    }
  }, []);

  const updateMusicState = useCallback(
    (state: MusicPlaybackState | null) => {
      if (!state) {
        setMusicState(null);
        setLiveMusicPosition(0);
        setIsMusicPaused(false);
        setCurrentSong(null);
        return;
      }

      setMusicState(state);
      setLiveMusicPosition(state.position_seconds);
      setIsMusicPaused(state.status !== "playing");
      setCurrentSong((previous) => {
        if (!state.matched_song) {
          return null;
        }
        const params = new URLSearchParams({ title: state.matched_song });
        const absoluteUrl = toAbsoluteUrl(`/smart-home/music/stream?${params.toString()}`);
        if (previous && previous.title === state.matched_song && previous.url === absoluteUrl) {
          return previous;
        }
        return { title: state.matched_song, url: absoluteUrl };
      });
    },
    []
  );

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

  const refreshMusicState = useCallback(async () => {
    try {
      const state = await apiClient<MusicPlaybackState>("/smart-home/music/state");
      updateMusicState(state);
    } catch (error) {
      console.error("Không thể tải trạng thái phát nhạc", error);
    }
  }, [updateMusicState]);

  const beginMusicPlayback = useCallback(
    async (title: string, streamUrl: string): Promise<boolean> => {
      const absoluteUrl = toAbsoluteUrl(streamUrl);
      let playbackStarted = false;
      const audioElement = audioPlayerRef.current;
      if (audioElement) {
        clearPendingAutoplayUnlock();
        try {
          audioElement.pause();
        } catch {
          // ignore pause errors
        }
        audioElement.autoplay = true;
        audioElement.playsInline = true;
        audioElement.preload = "auto";
        audioElement.src = absoluteUrl;

        const attemptPlayback = async (): Promise<boolean> => {
          try {
            audioElement.muted = false;
            await audioElement.play();
            return true;
          } catch (error) {
            if (error instanceof DOMException && error.name === "NotAllowedError") {
              const unmuteOnPlay = () => {
                audioElement.muted = false;
                audioElement.removeEventListener("playing", unmuteOnPlay);
              };
              try {
                audioElement.muted = true;
                audioElement.addEventListener("playing", unmuteOnPlay, { once: true });
                await audioElement.play();
                return true;
              } catch {
                audioElement.removeEventListener("playing", unmuteOnPlay);
                audioElement.muted = false;
                audioElement.pause();
              }
            }
            console.error("Không thể phát nhạc tự động", error);
            return false;
          }
        };

        const scheduleUnlock = () => {
          const resumePlayback = async () => {
            clearPendingAutoplayUnlock();
            try {
              audioElement.muted = false;
              await audioElement.play();
              showFeedback(`Đang phát bài: ${title}`);
            } catch (resumeError) {
              console.error("Không thể phát nhạc sau khi người dùng tương tác", resumeError);
              showFeedback("Không thể phát nhạc trên trình duyệt", true);
            }
          };
          const cleanup = () => {
            document.removeEventListener("click", resumePlayback);
            document.removeEventListener("keydown", resumePlayback);
          };
          document.addEventListener("click", resumePlayback, { once: true });
          document.addEventListener("keydown", resumePlayback, { once: true });
          autoplayUnlockCleanupRef.current = () => {
            cleanup();
            autoplayUnlockCleanupRef.current = null;
          };
        };

        playbackStarted = await attemptPlayback();
        if (!playbackStarted) {
          scheduleUnlock();
        }
      }
      setCurrentSong({ title, url: absoluteUrl });
      setIsMusicPaused(false);
      return playbackStarted;
    },
    [clearPendingAutoplayUnlock, showFeedback]
  );

  const pauseCurrentMusic = useCallback((): boolean => {
    const audioElement = audioPlayerRef.current;
    if (!audioElement) {
      return false;
    }
    try {
      isMusicControlFromServerRef.current = true;
      audioElement.pause();
      setIsMusicPaused(true);
      return true;
    } catch (error) {
      console.error("Không thể tạm dừng nhạc trên trình duyệt", error);
      return false;
    } finally {
      window.setTimeout(() => {
        isMusicControlFromServerRef.current = false;
      });
    }
  }, []);

  const resumeCurrentMusic = useCallback(async (): Promise<boolean> => {
    const audioElement = audioPlayerRef.current;
    if (!audioElement) {
      return false;
    }
    try {
      isMusicControlFromServerRef.current = true;
      await audioElement.play();
      setIsMusicPaused(false);
      return true;
    } catch (error) {
      console.error("Không thể tiếp tục phát nhạc trên trình duyệt", error);
      return false;
    } finally {
      window.setTimeout(() => {
        isMusicControlFromServerRef.current = false;
      });
    }
  }, []);

  const handleMusicPause = useCallback(async () => {
    if (isMusicControlFromServerRef.current) {
      return;
    }
    setIsMusicPaused(true);
    try {
      const state = await apiClient<MusicPlaybackState>("/smart-home/music/pause", {
        method: "POST"
      });
      updateMusicState(state);
    } catch (error) {
      console.error("Không thể cập nhật trạng thái tạm dừng", error);
    }
  }, [updateMusicState]);

  const handleMusicPlay = useCallback(async () => {
    if (isMusicControlFromServerRef.current) {
      return;
    }
    setIsMusicPaused(false);
    try {
      const state = await apiClient<MusicPlaybackState>("/smart-home/music/resume", {
        method: "POST"
      });
      updateMusicState(state);
    } catch (error) {
      console.error("Không thể cập nhật trạng thái phát nhạc", error);
    }
  }, [updateMusicState]);

  const handleMusicSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const title = musicTitle.trim();
      if (!title) {
        showFeedback("Vui lòng nhập tên bài hát", true);
        return;
      }

      try {
        const response = await apiClient<MusicPlaybackResponse>("/smart-home/music/play", {
          method: "POST",
          body: JSON.stringify({ title })
        });
        const playbackStarted = await beginMusicPlayback(response.selected_song, response.stream_url);
        updateMusicState(response.playback_state);
        if (playbackStarted) {
          showFeedback(`Đang phát bài: ${response.selected_song}`);
        } else {
          showFeedback(
            "Trình duyệt đang chặn phát nhạc tự động. Nhấp vào màn hình để bắt đầu phát.",
            true
          );
        }
        setMusicTitle("");
      } catch (error) {
        if (error instanceof Error) {
          showFeedback(error.message, true);
        }
      }
    },
    [beginMusicPlayback, musicTitle, showFeedback, updateMusicState]
  );

  useEffect(() => {
    refreshMusicLibrary();
    refreshMusicState();
  }, [refreshMusicLibrary, refreshMusicState]);

  useEffect(() => {
    if (!musicState) {
      setLiveMusicPosition(0);
      return;
    }

    if (musicState.status !== "playing") {
      setLiveMusicPosition(musicState.position_seconds);
      return;
    }

    let frame: number;
    const startTime = performance.now();
    const basePosition = musicState.position_seconds;

    const tick = () => {
      const elapsed = (performance.now() - startTime) / 1000;
      setLiveMusicPosition(basePosition + elapsed);
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [musicState]);

  useEffect(() => {
    const audioElement = audioPlayerRef.current;
    if (!audioElement) {
      return;
    }

    if (!musicState || !musicState.matched_song || !currentSong) {
      return;
    }

    const targetSrc = currentSong.url;
    if (audioElement.src !== targetSrc) {
      isMusicControlFromServerRef.current = true;
      audioElement.src = targetSrc;
      audioElement.load();
      window.setTimeout(() => {
        isMusicControlFromServerRef.current = false;
      });
    }

    const desiredTime = musicState.position_seconds;
    if (Number.isFinite(desiredTime)) {
      const duration = audioElement.duration;
      const clamped = Number.isFinite(duration) && duration > 0 ? Math.min(desiredTime, duration) : desiredTime;
      if (Math.abs(audioElement.currentTime - clamped) > 1) {
        audioElement.currentTime = clamped;
      }
    }

    if (musicState.status === "playing") {
      if (audioElement.paused) {
        isMusicControlFromServerRef.current = true;
        audioElement
          .play()
          .catch((error) => {
            console.warn("Không thể tự động phát nhạc", error);
          })
          .finally(() => {
            window.setTimeout(() => {
              isMusicControlFromServerRef.current = false;
            });
          });
      }
    } else if (!audioElement.paused) {
      isMusicControlFromServerRef.current = true;
      audioElement.pause();
      window.setTimeout(() => {
        isMusicControlFromServerRef.current = false;
      });
    }
  }, [currentSong, musicState]);

  useEffect(() => {
    let isMounted = true;

    const connect = () => {
      if (!isMounted || musicSocketRef.current) {
        return;
      }

      try {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(`${protocol}://${window.location.host}/smart-home/music/updates`);
        musicSocketRef.current = socket;

        socket.addEventListener("message", (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload.state && (payload.type === "snapshot" || payload.type === "update")) {
              updateMusicState(payload.state as MusicPlaybackState);
            }
          } catch (error) {
            console.error("Không thể phân tích dữ liệu trạng thái nhạc", error);
          }
        });

        socket.addEventListener("close", () => {
          if (musicSocketRef.current === socket) {
            musicSocketRef.current = null;
          }
          if (isMounted) {
            musicReconnectTimer.current = window.setTimeout(connect, 3000);
          }
        });

        socket.addEventListener("error", () => {
          socket.close();
        });
      } catch (error) {
        console.error("Không thể kết nối websocket nhạc", error);
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (musicReconnectTimer.current) {
        window.clearTimeout(musicReconnectTimer.current);
        musicReconnectTimer.current = null;
      }
      musicSocketRef.current?.close();
      musicSocketRef.current = null;
    };
  }, [updateMusicState]);

  useEffect(() => () => {
    clearPendingAutoplayUnlock();
  }, [clearPendingAutoplayUnlock]);

  const sortedLibrary = useMemo(
    () => [...musicLibrary].sort((a, b) => a.localeCompare(b, "vi", { sensitivity: "base" })),
    [musicLibrary]
  );

  return {
    musicState,
    liveMusicPosition,
    musicTitle,
    setMusicTitle,
    audioPlayerRef,
    currentSong,
    sortedLibrary,
    handleMusicSubmit,
    handleMusicPause,
    handleMusicPlay,
    setLiveMusicPosition,
    beginMusicPlayback,
    pauseCurrentMusic,
    resumeCurrentMusic,
    updateMusicState
  };
};
