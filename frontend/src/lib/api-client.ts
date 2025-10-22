export async function apiClient<TResponse>(url: string, options: RequestInit = {}): Promise<TResponse> {
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
