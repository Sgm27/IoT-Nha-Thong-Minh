export interface LightState {
  location: string;
  is_on: boolean;
}

export interface MusicPlaybackState {
  requested_title: string | null;
  matched_song: string | null;
  status: "stopped" | "playing" | "paused";
  position_seconds: number;
  duration_seconds: number | null;
  updated_at: number;
}

export interface MusicPlaybackResponse {
  selected_song: string;
  stream_url: string;
  playback_state: MusicPlaybackState;
}
