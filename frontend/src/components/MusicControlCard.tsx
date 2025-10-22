import { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatDuration } from "@/lib/format";
import type { MusicPlaybackState } from "@/types/smart-home";

interface MusicControlCardProps {
  musicState: MusicPlaybackState | null;
  liveMusicPosition: number;
  musicTitle: string;
  onMusicTitleChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  audioPlayerRef: React.RefObject<HTMLAudioElement>;
  currentSong: { title: string; url: string } | null;
  sortedLibrary: string[];
  onMusicPause: () => void;
  onMusicPlay: () => void;
  onTimeUpdate: (time: number) => void;
}

export function MusicControlCard({
  musicState,
  liveMusicPosition,
  musicTitle,
  onMusicTitleChange,
  onSubmit,
  audioPlayerRef,
  currentSong,
  sortedLibrary,
  onMusicPause,
  onMusicPlay,
  onTimeUpdate
}: MusicControlCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Phát nhạc</CardTitle>
        <CardDescription>Yêu cầu backend phát bài hát mong muốn.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-6">
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-2">
            <Label htmlFor="song-title">Tên bài hát</Label>
            <Input
              id="song-title"
              value={musicTitle}
              onChange={(event) => onMusicTitleChange(event.target.value)}
              placeholder="Nhập tên bài hát muốn nghe"
            />
          </div>
          <Button type="submit" className="w-full sm:w-auto">
            Tìm và phát
          </Button>
        </form>

        <div className="space-y-3">
          <div className="rounded-lg border bg-background p-4">
            <p className="text-sm font-semibold">
              {musicState?.matched_song
                ? `${musicState.status === "paused" ? "Đang tạm dừng" : "Đang phát"}: ${musicState.matched_song}`
                : "Chưa phát bài hát nào"}
            </p>
            <p className="text-xs text-muted-foreground">
              {musicState
                ? (() => {
                    const durationText = musicState.duration_seconds
                      ? ` / ${formatDuration(musicState.duration_seconds)}`
                      : "";
                    return `Thời gian: ${formatDuration(liveMusicPosition)}${durationText}`;
                  })()
                : "Đang chờ trạng thái phát nhạc từ máy chủ."}
            </p>
            <audio
              ref={audioPlayerRef}
              className="mt-3 w-full"
              autoPlay
              playsInline
              preload="auto"
              controls
              src={currentSong?.url}
              onPause={() => {
                onMusicPause();
              }}
              onPlay={() => {
                onMusicPlay();
              }}
              onTimeUpdate={(event) => {
                const element = event.currentTarget;
                onTimeUpdate(element.currentTime);
              }}
            >
              Trình duyệt của bạn không hỗ trợ phát nhạc.
            </audio>
            {!currentSong ? (
              <p className="mt-2 text-xs text-muted-foreground">Yêu cầu một bài hát để bắt đầu phát nhạc.</p>
            ) : null}
          </div>

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
  );
}
