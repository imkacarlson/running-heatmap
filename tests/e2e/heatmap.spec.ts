import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('PMTiles loads and lasso UI appears', async ({ page }) => {
  await page.waitForResponse(r =>
    r.url().includes('runs.pmtiles') && r.status() === 206);

  const center = { x: 400, y: 400 };
  await page.mouse.move(center.x, center.y);
  await page.mouse.down();
  await page.mouse.move(center.x + 50, center.y);
  await page.mouse.move(center.x + 50, center.y + 50);
  await page.mouse.move(center.x, center.y + 50);
  await page.mouse.up();

  await expect(page.locator('#side-panel')).toHaveClass(/open/);
  await expect(page.locator('#panel-content .run-card')).toHaveCountGreaterThan(0);
});
