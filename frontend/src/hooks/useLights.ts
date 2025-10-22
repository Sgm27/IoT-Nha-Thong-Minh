import { useCallback, useEffect, useRef, useState } from "react";

import { apiClient } from "@/lib/api-client";
import { normalizeLocation, sortLights } from "@/lib/lights";
import type { LightState } from "@/types/smart-home";

interface UseLightsOptions {
  showFeedback: (message: string, isError?: boolean) => void;
}

export const useLights = ({ showFeedback }: UseLightsOptions) => {
  const [lights, setLights] = useState<LightState[]>([]);
  const [lightLocation, setLightLocation] = useState<string>("");
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);

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

  useEffect(() => {
    refreshLights();
  }, [refreshLights]);

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
              applyLightUpdate(payload.light as LightState);
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

  return {
    lights,
    lightLocation,
    setLightLocation,
    handleLightAction,
    applyLightUpdate,
    refreshLights
  };
};
