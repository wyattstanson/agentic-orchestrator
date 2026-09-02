import { test, expect } from "@playwright/test";

test("desktop boots with the dock and Command Center", async ({ page }) => {
  await page.goto("/");
  // Command Center opens on boot (title in the menu bar + window content).
  await expect(page.getByText("Command Center").first()).toBeVisible();
  await expect(page.getByText(/running ·/).first()).toBeVisible();
  // The dock exposes all eight apps as labelled buttons.
  await expect(page.locator('button[aria-label="Trace Explorer"]')).toBeVisible();
  await expect(page.locator('button[aria-label="Tool Registry"]')).toBeVisible();
});

test("Tool Registry lists the backend's tools", async ({ page }) => {
  await page.goto("/");
  await page.locator('button[aria-label="Tool Registry"]').click();
  await expect(page.getByText("web_search").first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("python_exec").first()).toBeVisible();
});

test("submit a task and watch it run to a final answer", async ({ page }) => {
  await page.goto("/");
  await page.locator('button[aria-label="New Task"]').click();

  const textarea = page.locator("textarea").first();
  await textarea.fill("Compare two vendors pricing and flag hidden fees");
  await page.getByRole("button", { name: "Run task" }).click();

  // The plan streams in, then a final answer — proof the full backend ran.
  await expect(page.getByText("Final Answer").first()).toBeVisible({ timeout: 30_000 });
});

test("plan approval pauses the run and Review Queue can approve it", async ({ page }) => {
  await page.goto("/");
  await page.locator('button[aria-label="New Task"]').click();

  await page.getByRole("checkbox").check();
  await page.locator("textarea").first().fill("Reconcile the Q2 ledger and flag discrepancies");
  await page.getByRole("button", { name: "Run task" }).click();

  // It pauses awaiting approval.
  await expect(page.getByText(/Paused —/).first()).toBeVisible({ timeout: 20_000 });

  // Approve it from the Review Queue.
  await page.locator('button[aria-label="Review Queue"]').click();
  await page.getByRole("button", { name: "Approve" }).first().click();

  // The run resumes and finishes.
  await expect(page.getByText("Final Answer").first()).toBeVisible({ timeout: 30_000 });
});
