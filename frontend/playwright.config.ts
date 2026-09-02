import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests run against a live stack. Start it first:
 *   backend:  uvicorn app.api.main:app --port 8000   (in project15/backend)
 *   frontend: npm run dev                            (in project15/frontend)
 * or `docker compose up` from project15. Then: npx playwright test
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 40_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
