import { test, expect } from '@playwright/test';
test('health failure and WebGL fallback are truthful',async({page})=>{
 await page.route('**/api/health',route=>route.fulfill({status:503,body:'{}',contentType:'application/json'}));
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type:any,...args:any[]){if(String(type).startsWith('webgl'))return null;return original.call(this,type,...args as []);} as typeof original;});
 await page.goto('/');await expect(page.locator('.connection')).toContainText('Backend unavailable');await expect(page.locator('.scene-fallback')).toContainText('Spatial preview unavailable');await expect(page.locator('h1')).toBeVisible();
});
