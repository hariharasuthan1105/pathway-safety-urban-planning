import { test, expect } from '@playwright/test';

test('a stale initial session check cannot undo successful signup', async ({page}) => {
  let release!:()=>void;
  const gate=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/auth/me',async route=>{await gate;await route.fulfill({status:401,contentType:'application/json',body:'{"detail":"No initial session"}'});});
  await page.goto('/signup');
  await page.getByPlaceholder('Control Room Operator').fill('Session Race Operator');
  await page.getByPlaceholder('operator@urbanintel.in').fill(`race_${Date.now()}@example.com`);
  await page.locator('input[type=password]').nth(0).fill('LocalTestPassword123!');
  await page.locator('input[type=password]').nth(1).fill('LocalTestPassword123!');
  await page.locator('button[type=submit]').click();
  await expect(page.locator('h1')).toContainText('Session Race Operator');
  const completed=page.waitForResponse('**/api/auth/me');release();await completed;
  await page.locator('.app-sidebar a[href="/app/digital-twin"]').click();
  await expect(page.locator('h1')).toContainText('Metropolis workspace');
});

test.describe('Authentication & Route Guard E2E Flow (§4, §9)', () => {
  test('Unauthenticated user accessing protected route is redirected to login', async ({ page }) => {
    await page.goto('/app/overview');
    await expect(page).toHaveURL(/\/login/);
  });

  test('Complete Signup -> Authenticated Dashboard Access -> Logout flow', async ({ page }) => {
    const testEmail = `operator_${Date.now()}@urbanintel.in`;

    // 1. Open Signup page
    await page.goto('/signup');
    await expect(page.getByRole('heading', { name: 'Operator Sign Up' })).toBeVisible();

    // 2. Fill Signup form
    await page.fill('input[placeholder="Control Room Operator"]', 'E2E Test Operator');
    await page.fill('input[placeholder="operator@urbanintel.in"]', testEmail);
    const pwdInputs = page.locator('input[type="password"]');
    await pwdInputs.nth(0).fill('E2ESecurePassword123!');
    await pwdInputs.nth(1).fill('E2ESecurePassword123!');

    // 3. Submit Signup form
    await page.click('button[type="submit"]');

    // 4. Verify redirected to protected overview dashboard
    await expect(page).toHaveURL(/\/app\/overview/, { timeout: 10000 });
    await expect(page.locator('h1')).toContainText('E2E Test Operator');

    // 5. Logout
    await page.click('button[title="Sign Out"]');

    // 6. Verify redirected back to login page
    await expect(page).toHaveURL(/\/login/);

    // 7. Verify protected route access is now blocked
    await page.goto('/app/overview');
    await expect(page).toHaveURL(/\/login/);
  });
});
