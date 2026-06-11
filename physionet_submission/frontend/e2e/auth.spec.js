// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Authentication critical-path E2E tests.
 * Stable across UI changes — drive the login form via accessible labels.
 *
 * Requires the Flask backend running on :5000 with the seeded clinician
 * account (clinician / Clinician123!).
 */

test.describe('Authentication', () => {
  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login|\/$/);
    await expect(page.getByLabel('Username')).toBeVisible();
  });

  test('invalid credentials show an error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Username').fill('clinician');
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByRole('alert')).toBeVisible();
  });

  test('valid clinician login reaches the dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Username').fill('clinician');
    await page.getByLabel('Password').fill('Clinician123!');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
