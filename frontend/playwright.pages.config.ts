import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  testMatch: ['pages.spec.ts', 'scene-budget.spec.ts'],
  projects: [{name:'pages'}],
  workers: 1,
  retries: 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_PAGES_URL || 'http://127.0.0.1:5174',
    ...devices['Desktop Chrome'],
    launchOptions: process.env.PLAYWRIGHT_EXECUTABLE_PATH ? {executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH} : {},
  },
});
