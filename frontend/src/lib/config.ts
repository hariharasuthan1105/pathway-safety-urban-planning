// Configuration Loader (§13)
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  isProd: import.meta.env.PROD,
  ssePollIntervalMs: 3000,
};

if (config.isProd && !import.meta.env.VITE_API_BASE_URL) {
  console.warn('[Config Warning] VITE_API_BASE_URL is unset in production build.');
}
