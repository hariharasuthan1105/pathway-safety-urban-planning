import { pathToFileURL } from 'node:url';

const setting = 'GitHub repository Settings → Secrets and variables → Actions → Variables → VITE_API_BASE_URL';
export function validateBackendOrigin(value) {
  const input = value?.trim();
  const fail = () => { throw new Error(`Set ${setting} to an absolute public HTTPS origin without credentials, trailing slash, path, query or fragment; then rerun the workflow. An Actions secret does not populate vars.VITE_API_BASE_URL.`); };
  if (!input || !/^https:\/\//i.test(input)) fail();
  let url;
  try { url = new URL(input); } catch { fail(); }
  if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash || input.endsWith('/') || ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) fail();
  return url.origin;
}

export async function verifyBackend(value, fetchImpl = fetch, options = {}) {
  const origin = validateBackendOrigin(value);
  const { attempts = 1, wait = ms => new Promise(resolve => setTimeout(resolve, ms)), delayMs = 5000 } = options;
  let failure;
  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      const response = await fetchImpl(`${origin}/api/health`, { signal: AbortSignal.timeout(15000), redirect: 'error' });
      if (response.status !== undefined ? response.status !== 200 : !response.ok) throw new Error(`Backend health returned HTTP ${response.status}.`);
      let health;
      try { health = await response.json(); } catch { throw new Error('Backend health did not return valid JSON.'); }
      if (health?.status !== 'HEALTHY') throw new Error('Backend did not report HEALTHY.');
      return origin;
    } catch (error) {
      failure = error;
      if (attempt + 1 < attempts) await wait(delayMs);
    }
  }
  throw new Error(`Backend health check failed after ${attempts} attempt(s): ${failure?.message || 'Network failure'}. Publication stopped.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    if (process.argv.includes('--validate-only')) {
      validateBackendOrigin(process.env.VITE_API_BASE_URL);
      console.log('VITE_API_BASE_URL configuration is valid.');
    } else {
      const origin = await verifyBackend(process.env.VITE_API_BASE_URL, fetch, { attempts: 4 });
      console.log(`Verified ${origin}/api/health: HTTP 200, HEALTHY`);
    }
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
