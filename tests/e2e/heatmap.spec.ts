import { test, expect } from "@playwright/test";

test('PMTiles loads and lasso UI appears', async ({ page }) => {
  await Promise.all([
    page.waitForResponse(r =>
      r.url().includes('runs.pmtiles') && (r.status() === 200 || r.status() === 206)),
    page.goto('/')
  ]);

  // Focus map on the temporary dataset location
  await page.evaluate(() => {
    // @ts-ignore
    map.setCenter([0.5, 0.5]);
    // @ts-ignore
    map.setZoom(12);
  });

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
