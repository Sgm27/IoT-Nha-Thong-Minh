import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";

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

export default function App() {
  const [lights, setLights] = useState<LightState[]>([]);
  const [musicLibrary, setMusicLibrary] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  const [lightLocation, setLightLocation] = useState<string>("");
  const [musicTitle, setMusicTitle] = useState<string>("");
  const reconnectTimer = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

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
