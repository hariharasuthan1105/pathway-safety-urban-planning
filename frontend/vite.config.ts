import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({command,mode}) => {
  const env=loadEnv(mode,process.cwd(),'VITE_');
  const api=(process.env.VITE_API_BASE_URL??env.VITE_API_BASE_URL??'').trim();
  if(command==='build' && (!api || !/^https?:\/\//.test(api))) {
    throw new Error('Set VITE_API_BASE_URL to the deployed API origin before building. No production API proxy is configured.');
  }
  return {
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/events': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
  }
})
