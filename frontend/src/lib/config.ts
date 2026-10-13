// Configuration Loader (§13)
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
const sanitizedBaseUrl = (rawBaseUrl && rawBaseUrl.trim()) 
  ? rawBaseUrl.trim().replace(/\/+$/, '') 
  : import.meta.env.PROD ? '' : 'http://127.0.0.1:8000';

export const config = {
  apiBaseUrl: sanitizedBaseUrl,
  isProd: import.meta.env.PROD,
  ssePollIntervalMs: 3000,
};

if (config.isProd && !rawBaseUrl?.trim()) {
  throw new Error('Production API origin is missing. Set VITE_API_BASE_URL and rebuild.');
}

