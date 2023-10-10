import { test, expect } from "playwright-test-coverage";

test('test', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Create Timer' }).click();
  await page.getByPlaceholder('Name').click();
  await page.getByPlaceholder('Name').fill('example');
  await page.getByPlaceholder('Name').press('Tab');
  await page.getByPlaceholder('12:00:00').fill('15:00:00');
  await page.getByPlaceholder('12:00:00').press('Tab');
  await page.getByPlaceholder('12:00:00').press('Tab');
  await page.getByRole('textbox').nth(3).fill('10:00');
  await page.getByRole('button', { name: 'Add' }).click();
});