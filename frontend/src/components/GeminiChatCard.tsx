import { ChangeEvent, FormEvent, KeyboardEvent, type CSSProperties } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatFileSize } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";

interface GeminiChatCardProps {
  geminiStatus: string;
  isGeminiConnected: boolean;
  isRecording: boolean;
  toggleRecording: () => void;
  isMicPermissionDenied: boolean;
  recordingError: string | null;
  isCameraStreaming: boolean;
  toggleCameraStream: () => void;
  cameraError: string | null;
  handleImageSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  imageInputRef: React.RefObject<HTMLInputElement>;
  selectedImagePreview: string | null;
  selectedImage: File | null;
  clearSelectedImage: () => void;
  sendSelectedImage: () => Promise<void> | void;
  isUploadingImage: boolean;
  chatMessages: ChatMessage[];
  chatContainerRef: React.RefObject<HTMLDivElement>;
  chatInput: string;
  onChatInputChange: (value: string) => void;
  onChatSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onChatKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
  maxImageSize: number;
  cameraVideoRef: React.RefObject<HTMLVideoElement>;
  cameraDimensions: { width: number; height: number } | null;
}

export function GeminiChatCard({
  geminiStatus,
  isGeminiConnected,
  isRecording,
  toggleRecording,
  isMicPermissionDenied,
  recordingError,
  isCameraStreaming,
  toggleCameraStream,
  cameraError,
  handleImageSelect,
  imageInputRef,
  selectedImagePreview,
  selectedImage,
  clearSelectedImage,
  sendSelectedImage,
  isUploadingImage,
  chatMessages,
  chatContainerRef,
  chatInput,
  onChatInputChange,
  onChatSubmit,
  onChatKeyDown,
  maxImageSize,
  cameraVideoRef,
  cameraDimensions
}: GeminiChatCardProps) {
  const aspectRatioStyle: CSSProperties = {
    aspectRatio: "4 / 3"
  };

  return (
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
              <Button type="button" variant={isRecording ? "default" : "secondary"} onClick={toggleRecording} disabled={!isGeminiConnected}>
                {isRecording ? "Tắt micro" : "Bật micro"}
              </Button>
              <span className="text-xs text-muted-foreground">
                {isRecording ? "Đang ghi âm và gửi tới Gemini" : "Nhấn để trò chuyện với Gemini bằng giọng nói"}
              </span>
            </div>
            {!isGeminiConnected ? (
              <span className="text-xs text-muted-foreground">Cần kết nối Gemini để sử dụng micro</span>
            ) : null}
          </div>
          {isMicPermissionDenied ? (
            <p className="text-xs text-destructive">Truy cập micro bị từ chối. Vui lòng kiểm tra quyền của trình duyệt.</p>
          ) : null}
          {recordingError ? <p className="text-xs text-destructive">{recordingError}</p> : null}
        </div>

        <div className="flex flex-col gap-3 rounded-lg border bg-background px-4 py-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant={isCameraStreaming ? "default" : "secondary"}
                onClick={toggleCameraStream}
                disabled={!isGeminiConnected}
              >
                {isCameraStreaming ? "Tắt camera" : "Bật camera"}
              </Button>
              <span className="text-xs text-muted-foreground">
                {isCameraStreaming
                  ? "Đang gửi hình ảnh từ camera tới Gemini"
                  : "Nhấn để chia sẻ hình ảnh trực tiếp với Gemini"}
              </span>
            </div>
            {!isGeminiConnected ? (
              <span className="text-xs text-muted-foreground">Cần kết nối Gemini để sử dụng camera</span>
            ) : null}
          </div>
          {cameraError ? <p className="text-xs text-destructive">{cameraError}</p> : null}
          <div className="relative mx-auto w-full max-w-md">
            <div className="relative w-full overflow-hidden" style={aspectRatioStyle}>
              <video
                ref={cameraVideoRef}
                className={cn(
                  "absolute inset-0 h-full w-full rounded-md border bg-black object-cover transition-opacity",
                  isCameraStreaming ? "opacity-100" : "pointer-events-none opacity-0"
                )}
                style={{ transform: "scaleX(-1)" }}
                autoPlay
                muted
                playsInline
              />
              <div
                className={cn(
                  "absolute inset-0 flex items-center justify-center rounded-md border border-dashed bg-background/90 text-xs text-muted-foreground transition-opacity",
                  isCameraStreaming ? "pointer-events-none opacity-0" : "opacity-100"
                )}
              >
                Camera đang tắt
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-background px-4 py-3 text-sm">
          <div className="flex flex-col gap-3">
            <div className="space-y-2">
              <Label htmlFor="gemini-image-upload">Gửi ảnh tới Gemini</Label>
              <Input
                id="gemini-image-upload"
                ref={imageInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                disabled={!isGeminiConnected || isUploadingImage}
              />
              <p className="text-xs text-muted-foreground">Hỗ trợ ảnh tối đa {formatFileSize(maxImageSize)}.</p>
            </div>
            {selectedImagePreview ? (
              <div className="flex flex-col gap-2">
                <img src={selectedImagePreview} alt="Ảnh đã chọn để gửi tới Gemini" className="max-h-48 rounded-md border object-contain" />
                {selectedImage ? (
                  <span className="text-xs text-muted-foreground">
                    {selectedImage.name} · {formatFileSize(selectedImage.size)}
                  </span>
                ) : null}
              </div>
            ) : null}
            <div className="flex justify-end gap-2">
              {selectedImage ? (
                <Button type="button" variant="ghost" onClick={clearSelectedImage} disabled={isUploadingImage}>
                  Bỏ chọn
                </Button>
              ) : null}
              <Button
                type="button"
                onClick={() => void sendSelectedImage()}
                disabled={!selectedImage || !isGeminiConnected || isUploadingImage}
              >
                {isUploadingImage ? "Đang gửi..." : "Gửi ảnh"}
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-hidden rounded-lg border bg-background">
          <div ref={chatContainerRef} className="h-80 space-y-4 overflow-y-auto p-4 text-sm">
            {chatMessages.length ? (
              chatMessages.map((message) => (
                <div key={message.id} className={cn("flex flex-col gap-1", message.role === "user" ? "items-end" : "items-start")}> 
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
                    <div className="flex flex-col gap-2">
                      {message.content ? (
                        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      ) : null}
                      {message.imageDataUrl ? (
                        <img
                          src={message.imageDataUrl}
                          alt={message.role === "user" ? "Ảnh bạn đã gửi" : "Ảnh từ Gemini"}
                          className="max-h-64 rounded-md border object-contain"
                        />
                      ) : null}
                    </div>
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

        <form className="flex flex-col gap-3" onSubmit={onChatSubmit}>
          <label className="space-y-2">
            <span className="text-sm font-medium">Tin nhắn</span>
            <textarea
              value={chatInput}
              onChange={(event) => onChatInputChange(event.target.value)}
              onKeyDown={onChatKeyDown}
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
  );
}
