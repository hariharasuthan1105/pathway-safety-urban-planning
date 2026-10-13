import { config } from './config';

let sessionToken: string | null = null;
export function setSessionToken(value: string | null) { sessionToken = value; }
const sessionHeaders = (): Record<string,string> => sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {};


export class ApiError extends Error {
  status: number;
  data?: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

interface FetchOptions extends RequestInit {
  timeoutMs?: number;
  retries?: number;
}

export async function fetchApi<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { timeoutMs = 8000, retries = 2, ...customConfig } = options;
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = endpoint.startsWith('http') ? endpoint : `${config.apiBaseUrl}${path}`;
  if (new URL(url).origin !== new URL(config.apiBaseUrl).origin) {
    throw new ApiError(0, 'API requests must use the configured backend origin');
  }

  const defaultHeaders: HeadersInit = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  };

  const requestConfig: RequestInit = {
    ...customConfig,
    credentials: 'include',
    headers: {
      ...defaultHeaders,
      ...sessionHeaders(),
      ...customConfig.headers,
    },
  };

  let attempt = 0;
  while (attempt <= (customConfig.method && customConfig.method !== 'GET' ? 0 : retries)) {
    attempt++;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, { ...requestConfig, signal: controller.signal });
      clearTimeout(timer);

      if (response.status === 401) {
        if (typeof window !== 'undefined' && !endpoint.includes('/api/auth/me')) {
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(401, errorData.detail || 'Session expired or unauthorized', errorData);
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(response.status, errorData.detail || `HTTP Error ${response.status}`, errorData);
      }

      if (response.status === 204) return undefined as T;
      return await response.json();
    } catch (err: any) {
      clearTimeout(timer);
      if (err.name === 'ApiError') throw err;

      if (attempt > retries || (customConfig.method && customConfig.method !== 'GET')) {
        throw new ApiError(0, err.message || 'Network request failed');
      }

      await new Promise(res => setTimeout(res, 500 * Math.pow(2, attempt - 1)));
    }
  }

  throw new ApiError(0, 'Request failed after retries');
}

// EventSource cannot carry Authorization. Keep streaming and polling on one origin.
export function subscribeState(onUpdate: () => void): () => void {
  const controller = new AbortController();
  void (async () => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/stream`, {
        credentials: 'include', headers: sessionHeaders(), signal: controller.signal,
      });
      if (response.status === 401) {
        window.dispatchEvent(new CustomEvent('auth:expired'));
        return;
      }
      if (!response.ok || !response.body) return;
      const reader = response.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      try {
        while (!controller.signal.aborted) {
          const {done, value} = await reader.read();
          if (done) break;
          buffer = (buffer + decoder.decode(value, {stream:true})).replaceAll('\r\n', '\n');
          let boundary;
          while ((boundary = buffer.indexOf('\n\n')) >= 0) {
            const event = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
            if (event.includes('event: state_update')) onUpdate();
          }
          if (buffer.length > 1048576) throw new Error('Stream frame exceeded limit');
        }
      } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
    } catch { /* Polling remains active when streaming is unavailable. */ }
  })();
  return () => controller.abort();
}
