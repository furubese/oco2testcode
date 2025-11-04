import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60 * 1000,
  expect: {
    timeout: 10000
  },
  fullyParallel: true,
  retries: 0,
  workers: undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
  use: {
    baseURL: process.env.CLOUDFRONT_URL || 'https://dy0dc92sru60q.cloudfront.net',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
