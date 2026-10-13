import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateBackendOrigin } from './verify-backend.mjs';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const origin = validateBackendOrigin(process.env.VITE_API_BASE_URL);
const base = process.env.VITE_BASE_PATH || '/pathway-safety-urban-planning/';
const html = readFileSync(resolve(dist, 'index.html'), 'utf8');
const assets = [...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)].map(m => m[1]);
if (!assets.length || assets.some(path => !path.startsWith(`${base}assets/`))) throw Error('Pages artifact has incorrect asset base paths.');
const scripts = readdirSync(resolve(dist, 'assets')).filter(name => name.endsWith('.js'));
let hasOrigin = false;
for (const name of scripts) {
  const text = readFileSync(resolve(dist, 'assets', name), 'utf8');
  if (/localhost|127\.0\.0\.1|:8000/.test(text)) throw Error(`Forbidden loopback string in production asset ${name}`);
  hasOrigin ||= text.includes(origin);
}
if (!hasOrigin) throw Error('Verified API origin was not embedded in the production artifact.');
console.log(`ARTIFACT_OK scripts=${scripts.length} base=${base} verifiedOrigin=true loopback=false`);
