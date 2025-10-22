import type { LightState } from "@/types/smart-home";

export const normalizeLocation = (location: string) => location.trim().toLowerCase();

export const sortLights = (lights: LightState[]) =>
  [...lights].sort((a, b) => a.location.localeCompare(b.location, "vi", { sensitivity: "base" }));
