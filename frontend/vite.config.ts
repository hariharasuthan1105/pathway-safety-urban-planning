import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({command,mode}) => {
  const env=loadEnv(mode,process.cwd(),'VITE_');
  const api=(process.env.VITE_API_BASE_URL??env.VITE_API_BASE_URL??'').trim();
  const pages=(process.env.VITE_DEPLOY_TARGET??env.VITE_DEPLOY_TARGET)==='github-pages';
  const base=(process.env.VITE_BASE_PATH??env.VITE_BASE_PATH??'/').trim();
  if (!/^\/(?!\/)[^?#]*\/$/.test(base) && base !== '/') {
    throw new Error('VITE_BASE_PATH must be an absolute path ending in /.');
  }
  if(command==='build') {
    let origin: URL;
    try { origin=new URL(api); } catch { throw new Error('Set VITE_API_BASE_URL to a valid API origin before building.'); }
    if(!['http:','https:'].includes(origin.protocol) || origin.username || origin.password || origin.pathname!=='/' || origin.search || origin.hash) {
      throw new Error('VITE_API_BASE_URL must be an HTTP(S) origin without credentials, path, query or fragment.');
    }
    if(pages && (origin.protocol!=='https:' || ['localhost','127.0.0.1','[::1]'].includes(origin.hostname))) {
      throw new Error('GitHub Pages requires a verified public HTTPS backend origin; loopback API targets are forbidden.');
    }
  }
  return {
  base,
  plugins: [react(), tailwindcss(), {
    name: 'router-inert-url-base',
    apply: 'build',
    transform(code, id) {
      // React Router's URL parser uses a loopback sentinel when no window is
      // supplied. It is not an API endpoint. Keep the production artifact free
      // of loopback strings by using a reserved, non-routable parsing origin.
      if (id.replaceAll('\\', '/').includes('/node_modules/react-router/')) {
        return { code: code.replaceAll('http://localhost', 'https://router.invalid'), map: null };
      }
    },
  }],
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
