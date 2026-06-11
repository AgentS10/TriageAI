// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * TriageAI — Playwright E2E configuration.
 *
 * Runs the React dev server automatically and points tests at it. The Flask
 * backend must be running separately on :5000 (the CRA proxy forwards /api):
 *
 *   # terminal 1
 *   python backend/seed_db.py && python backend/app.py
 *   # terminal 2
 *   cd frontend && npm run test:e2e
 */
module.exports = defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: { BROWSER: 'none' },
  },
});
