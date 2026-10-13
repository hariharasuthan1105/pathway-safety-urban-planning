import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', testMatch: 'cookie-independent.spec.ts', workers: 1,
  use: {baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5176'},
  projects: [
    {name:'chromium',use:{...devices['Desktop Chrome']}},
    {name:'firefox',use:{...devices['Desktop Firefox']}},
    {name:'webkit',use:{...devices['Desktop Safari']}},
  ],
});
