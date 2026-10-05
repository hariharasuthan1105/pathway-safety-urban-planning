import { config } from './config';

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
