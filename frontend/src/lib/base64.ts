export const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
};

export const isLikelyBase64String = (value: string) => {
  if (!value || value.length % 4 !== 0) {
    return false;
  }

  let padding = 0;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code === 61) {
      padding += 1;
      if (padding > 2) {
        return false;
      }
      const remaining = value.length - index;
      if (remaining > 2) {
        return false;
      }
      continue;
    }
    if (
      (code >= 65 && code <= 90) ||
      (code >= 97 && code <= 122) ||
      (code >= 48 && code <= 57) ||
      code === 43 ||
      code === 47
    ) {
      continue;
    }
    return false;
  }

  return true;
};

export const base64ToArrayBuffer = (base64: string): ArrayBuffer | null => {
  if (!base64) {
    return null;
  }

  let binary: string;
  try {
    binary = atob(base64);
  } catch {
    return null;
  }

  let depth = 0;
  while (depth < 2 && isLikelyBase64String(binary)) {
    depth += 1;
    try {
      const decoded = atob(binary);
      if (!decoded || decoded === binary) {
        break;
      }
      binary = decoded;
    } catch {
      break;
    }
  }

  const byteCount = binary.length;
  if (byteCount === 0) {
    return null;
  }

  const bytes = new Uint8Array(byteCount);
  for (let index = 0; index < byteCount; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes.buffer;
};
