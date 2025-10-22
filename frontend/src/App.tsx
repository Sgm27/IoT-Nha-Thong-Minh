import { useCallback, useState } from "react";

import { LightControlCard } from "@/components/LightControlCard";
import { GeminiChatCard } from "@/components/GeminiChatCard";
import { MusicControlCard } from "@/components/MusicControlCard";
import { GEMINI_MAX_IMAGE_SIZE, useGeminiRealtime } from "@/hooks/useGeminiRealtime";
import { useLights } from "@/hooks/useLights";
import { useMusicController } from "@/hooks/useMusicController";
import { cn } from "@/lib/utils";

interface FeedbackState {
  message: string;
  isError?: boolean;
}

export default function App() {
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  const showFeedback = useCallback((message: string, isError = false) => {
    setFeedback({ message, isError });
  }, []);

  const { lights, lightLocation, setLightLocation, handleLightAction, applyLightUpdate } = useLights({
    showFeedback
  });

  const {
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
    resumeCurrentMusic
  } = useMusicController({ showFeedback });

  const {
    geminiStatus,
    isGeminiConnected,
    chatMessages,
    chatInput,
    setChatInput,
    handleChatSubmit,
    handleChatKeyDown,
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
    cameraError
  } = useGeminiRealtime({
    showFeedback,
    onLightUpdate: applyLightUpdate,
    beginMusicPlayback,
    pauseCurrentMusic,
    resumeCurrentMusic
  });

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
          <LightControlCard
            lights={lights}
            lightLocation={lightLocation}
            onLightLocationChange={setLightLocation}
            onLightAction={handleLightAction}
          />
          <MusicControlCard
            musicState={musicState}
            liveMusicPosition={liveMusicPosition}
            musicTitle={musicTitle}
            onMusicTitleChange={setMusicTitle}
            onSubmit={handleMusicSubmit}
            audioPlayerRef={audioPlayerRef}
            currentSong={currentSong}
            sortedLibrary={sortedLibrary}
            onMusicPause={() => {
              void handleMusicPause();
            }}
            onMusicPlay={() => {
              void handleMusicPlay();
            }}
            onTimeUpdate={setLiveMusicPosition}
          />
        </div>

        <GeminiChatCard
          geminiStatus={geminiStatus}
          isGeminiConnected={isGeminiConnected}
          isRecording={isRecording}
          toggleRecording={toggleRecording}
          isMicPermissionDenied={isMicPermissionDenied}
          recordingError={recordingError}
          isCameraStreaming={isCameraStreaming}
          toggleCameraStream={toggleCameraStream}
          cameraError={cameraError}
          handleImageSelect={handleImageSelect}
          imageInputRef={imageInputRef}
          selectedImagePreview={selectedImagePreview}
          selectedImage={selectedImage}
          clearSelectedImage={clearSelectedImage}
          sendSelectedImage={sendSelectedImage}
          isUploadingImage={isUploadingImage}
          chatMessages={chatMessages}
          chatContainerRef={chatContainerRef}
          chatInput={chatInput}
          onChatInputChange={setChatInput}
          onChatSubmit={handleChatSubmit}
          onChatKeyDown={handleChatKeyDown}
          maxImageSize={GEMINI_MAX_IMAGE_SIZE}
          cameraVideoRef={cameraVideoRef}
        />

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
