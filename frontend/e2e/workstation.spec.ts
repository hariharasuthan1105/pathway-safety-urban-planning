import { test, expect } from '@playwright/test';

test('landing renders procedural WebGL scene and mobile layout', async ({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.locator('h1')).toContainText('SEE THE CITY.');
 await expect(page.locator('canvas')).toBeVisible();await expect(page.locator('.scene-loading')).toHaveCount(0);
 await page.getByRole('button',{name:'Pause camera motion'}).click();await page.getByRole('button',{name:'Reset camera'}).click();
 await page.screenshot({path:'../../../outputs/landing-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});
 await expect(page.getByRole('heading',{name:/SEE THE CITY/})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 expect(await page.locator('.pixel-accent').first().evaluate(el=>getComputedStyle(el).animationName)).toBe('none');
 await page.screenshot({path:'../../../outputs/landing-mobile.png',fullPage:true});expect(errors).toEqual([]);
});

test('workstation routes, geographic selection, command palette and Copilot',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/signup');await page.getByPlaceholder('Control Room Operator').fill('Spatial QA Operator');await page.getByPlaceholder('operator@urbanintel.in').fill(`spatial_${Date.now()}@example.com`);await page.locator('input[type=password]').nth(0).fill('LocalTestPassword123!');await page.locator('input[type=password]').nth(1).fill('LocalTestPassword123!');await page.locator('button[type=submit]').click();await expect(page).toHaveURL(/app\/overview/);
 await expect(page.locator('.city-marker').first()).toBeVisible();
 await page.getByLabel('Selected city',{exact:true}).selectOption('Chennai');await expect(page.locator('.inspection')).toContainText('13.0827, 80.2707');await expect(page.locator('.reticle')).toHaveCount(1);await expect(page.locator('.map-canvas')).toHaveAttribute('data-center','13.08270,80.27070');
 await page.screenshot({path:'../../../outputs/dashboard-desktop.png',fullPage:true});
 for(const [route,title] of [['cities','Cities explorer'],['traffic','Traffic intelligence'],['risk','Risk intelligence'],['environment','Environmental intelligence'],['events','Event investigation'],['settings','Workspace settings']]){await page.locator(`.app-sidebar a[href="/app/${route}"]`).click();await expect(page.locator('h1')).toContainText(title);}
 await page.keyboard.press('Control+k');await expect(page.getByRole('dialog')).toBeVisible();await page.getByLabel('Search commands and cities').fill('Kochi');await page.getByRole('dialog').getByRole('button',{name:/Kochi/}).click();await expect(page).toHaveURL(/app\/cities/);await expect(page.locator('.inspection')).toContainText('9.9312, 76.2673');
 await page.locator('.app-sidebar a[href="/app/copilot"]').click();await page.getByLabel('Ask the Urban Copilot').fill('Why is Kochi at risk?');await page.getByLabel('Send question').click();await expect(page.locator('.answer-turn')).toBeVisible({timeout:30000});await expect(page.locator('.answer-turn')).toContainText('DETERMINISTIC FALLBACK');
 await page.screenshot({path:'../../../outputs/copilot-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.getByLabel('Toggle navigation').click();await page.locator('.app-sidebar a[href="/app/events"]').click();await expect(page.locator('h1')).toContainText('Event investigation');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:'../../../outputs/dashboard-mobile.png',fullPage:true});expect(errors).toEqual([]);
});
