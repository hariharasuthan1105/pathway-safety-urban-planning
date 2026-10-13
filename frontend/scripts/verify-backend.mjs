// Deployment preflight. Merely building the UI does not establish API health.
const value = process.env.VITE_API_BASE_URL?.trim();
try {
  const origin = new URL(value || '');
  if (origin.protocol !== 'https:' || origin.username || origin.password ||
      origin.pathname !== '/' || origin.search || origin.hash ||
      ['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname)) {
    throw new Error('Set VITE_API_BASE_URL to the verified public HTTPS backend origin.');
  }
  const response = await fetch(`${origin.origin}/api/health`, { signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Backend health returned HTTP ${response.status}. Publication stopped.`);
  const health = await response.json();
  if (health.status !== 'HEALTHY') throw new Error('Backend did not report HEALTHY. Publication stopped.');
  console.log(`Verified ${origin.origin}/api/health: HTTP 200, HEALTHY`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
