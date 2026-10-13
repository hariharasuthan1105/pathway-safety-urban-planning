import type { Page } from '@playwright/test';

// Compiled builds keep their real configured origin. Browser tests intercept
// requests so signup and all other mutations reach only the isolated QA server.
export async function useLocalApi(page: Page) {
  const origin=process.env.VITE_API_BASE_URL;
  const local=process.env.TEST_API_ORIGIN || 'http://127.0.0.1:10003';
  if(!origin) throw new Error('Set VITE_API_BASE_URL to the origin embedded in dist');
  if(!['127.0.0.1','localhost'].includes(new URL(local).hostname)) throw new Error('QA API must be local');
  await page.route('**/api/**',async route=>{
    if(!route.request().url().startsWith(`${origin}/api/`)) {await route.abort();return;}
    if(route.request().url().endsWith('/api/stream')) {
      await route.fulfill({status:200,contentType:'text/event-stream',body:''});return;
    }
    const url=new URL(route.request().url());
    const response=await route.fetch({url:`${local}${url.pathname}${url.search}`});
    await route.fulfill({response});
  });
  return origin;
}
