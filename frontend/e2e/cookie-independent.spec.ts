import {test,expect} from '@playwright/test';

test('protected API and logout work when session cookies are unavailable',async({page,context})=>{
  test.setTimeout(60000);
  const errors:string[]=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/signup');
  await page.getByPlaceholder('Control Room Operator').fill('Cookie independent operator');
  await page.getByPlaceholder('operator@urbanintel.in').fill(`memory_${Date.now()}@example.test`);
  await page.locator('input[type=password]').nth(0).fill('LocalTransportCheck123!');
  await page.locator('input[type=password]').nth(1).fill('LocalTransportCheck123!');
  const stream = page.waitForResponse('**/api/stream');
  await page.locator('button[type=submit]').click();
  await expect(page).toHaveURL(/app\/overview/);
  const streaming = await stream;
  expect(streaming.status()).toBe(200);
  expect(streaming.request().headers()['authorization']).toMatch(/^Bearer /);
  await context.clearCookies();
  const stateRequest=page.waitForRequest(r=>r.url().endsWith('/api/state') && !!r.headers()['authorization']);
  await page.getByLabel('Refresh telemetry').click();
  const request=await stateRequest;
  expect((await (await request.response())!.json()).city_summaries).toBeTruthy();
  const logout=page.waitForResponse('**/api/auth/logout');
  await page.getByTitle('Sign Out').click();
  expect((await logout).status()).toBe(200);
  await expect(page).toHaveURL(/login/);
  const revoked=await context.request.get(request.url(),{headers:{Authorization:request.headers()['authorization']}});
  expect(revoked.status()).toBe(401);
  expect(await page.evaluate(()=>localStorage.length+sessionStorage.length)).toBe(0);
  expect(errors).toEqual([]);
});

test('eight-second polling recovers when authenticated streaming is unavailable',async({page})=>{
  test.setTimeout(45000);
  await page.route('**/api/stream',route=>route.abort());
  await page.goto('/signup');
  await page.getByPlaceholder('Control Room Operator').fill('Polling operator');
  await page.getByPlaceholder('operator@urbanintel.in').fill(`poll_${Date.now()}@example.test`);
  await page.locator('input[type=password]').nth(0).fill('LocalTransportCheck123!');
  await page.locator('input[type=password]').nth(1).fill('LocalTransportCheck123!');
  const first=page.waitForResponse('**/api/state');
  await page.locator('button[type=submit]').click();
  expect((await first).status()).toBe(200);
  const started=Date.now();
  const next=await page.waitForResponse('**/api/state',{timeout:12000});
  expect(next.status()).toBe(200);
  expect(Date.now()-started).toBeGreaterThan(5000);
});
