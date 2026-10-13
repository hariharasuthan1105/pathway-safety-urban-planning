// Deployment preflight. Merely building the UI does not establish API health.
const value = process.env.VITE_API_BASE_URL?.trim();
try {
  if (!value) {
    throw new Error(
      'Missing VITE_API_BASE_URL repository variable. ' +
      'Please configure VITE_API_BASE_URL in GitHub repository Settings -> Secrets and variables -> Actions -> Variables ' +
      'with your verified public HTTPS backend origin (e.g. https://your-backend.onrender.com).'
    );
  }

  let origin;
  try {
    origin = new URL(value);
  } catch {
    throw new Error(
      `Malformed VITE_API_BASE_URL: "${value}". ` +
      'Must be a valid HTTPS URL (e.g. https://your-backend.onrender.com).'
    );
  }

  if (origin.protocol !== 'https:' || origin.username || origin.password ||
      origin.pathname !== '/' || origin.search || origin.hash ||
      ['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname)) {
    throw new Error(
      `Invalid VITE_API_BASE_URL: "${value}". ` +
      'Must be a public HTTPS origin without path, query, hash, or localhost/loopback addresses.'
    );
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
