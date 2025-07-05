import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:5000',
    headless: true,
    viewport: { width: 1280, height: 800 },
  },
});
