// Configuration Loader (§13)
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
const sanitizedBaseUrl = (rawBaseUrl && rawBaseUrl.trim()) 
  ? rawBaseUrl.trim().replace(/\/+$/, '') 
  : 'http://localhost:8000';

export const config = {
  apiBaseUrl: sanitizedBaseUrl,
  isProd: import.meta.env.PROD,
  ssePollIntervalMs: 3000,
};

if (config.isProd && !import.meta.env.VITE_API_BASE_URL) {
  console.warn('[Config Warning] VITE_API_BASE_URL is unset in production build.');
}

