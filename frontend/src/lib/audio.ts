import { OUTPUT_SAMPLE_RATE } from "@/constants/gemini";

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

export const concatFloat32 = (existing: Float32Array | null, incoming: Float32Array) => {
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

export const resampleFloat32 = (input: Float32Array, sourceRate: number, targetRate: number) => {
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

export const float32ToPCM16 = (input: Float32Array) => {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);
  for (let index = 0; index < input.length; index += 1) {
    const value = clamp(input[index], -1, 1);
    const intSample = value < 0 ? value * 0x8000 : value * 0x7fff;
    view.setInt16(index * 2, Math.round(intSample), true);
  }
  return buffer;
};

const hasContainerHeader = (buffer: ArrayBuffer) => {
  if (!buffer || buffer.byteLength < 4) {
    return false;
  }

  const headerBytes = new Uint8Array(buffer.slice(0, 4));
  const signature = String.fromCharCode(...headerBytes);
  if (signature === "RIFF" || signature === "OggS" || signature === "fLaC") {
    return true;
  }
  return signature.startsWith("ID3");
};

const mimeSuggestsContainer = (mimeType?: string) => {
  if (!mimeType) {
    return false;
  }
  const normalized = mimeType.toLowerCase();
  if (normalized.includes("pcm")) {
    return false;
  }
  return (
    normalized.includes("ogg") ||
    normalized.includes("mp3") ||
    normalized.includes("webm") ||
    normalized.includes("wav") ||
    normalized.includes("flac")
  );
};

export const decodeAudioChunk = async (
  buffer: ArrayBuffer,
  context: AudioContext,
  sourceSampleRate: number,
  mimeType?: string
): Promise<AudioBuffer | null> => {
  if (!buffer || buffer.byteLength === 0) {
    return null;
  }

  const shouldUseDecoder = mimeSuggestsContainer(mimeType) || hasContainerHeader(buffer);
  if (shouldUseDecoder) {
    try {
      return await context.decodeAudioData(buffer.slice(0));
    } catch (error) {
      console.warn("Falling back to PCM decode for Gemini audio chunk", error);
    }
  }

  const effectiveSampleRate =
    typeof sourceSampleRate === "number" && Number.isFinite(sourceSampleRate) && sourceSampleRate > 0
      ? sourceSampleRate
      : OUTPUT_SAMPLE_RATE;

  const isFloat32PCM = Boolean(mimeType && mimeType.toLowerCase().includes("bit=32"));
  const bytesPerSample = isFloat32PCM ? 4 : 2;
  const remainder = buffer.byteLength % bytesPerSample;
  const alignedBuffer = remainder === 0 ? buffer : buffer.slice(0, buffer.byteLength - remainder);

  if (alignedBuffer.byteLength === 0) {
    return null;
  }

  let channelData: Float32Array;
  if (isFloat32PCM) {
    const floatView = new Float32Array(alignedBuffer);
    channelData = floatView.length > 0 ? floatView.slice() : new Float32Array();
  } else {
    let pcm16: Int16Array;
    try {
      pcm16 = new Int16Array(alignedBuffer);
    } catch {
      return null;
    }
    if (pcm16.length === 0) {
      return null;
    }
    channelData = new Float32Array(pcm16.length);
    for (let index = 0; index < pcm16.length; index += 1) {
      channelData[index] = pcm16[index] / 32768;
    }
  }

  if (channelData.length === 0) {
    return null;
  }

  const targetSampleRate = context.sampleRate || effectiveSampleRate;
  const resampled =
    targetSampleRate === effectiveSampleRate
      ? channelData
      : resampleFloat32(channelData, effectiveSampleRate, targetSampleRate);

  const audioBuffer = context.createBuffer(1, resampled.length, targetSampleRate);
  audioBuffer.copyToChannel(resampled, 0);
  return audioBuffer;
};

export const extractSampleRate = (mimeType?: string, fallback?: number) => {
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
