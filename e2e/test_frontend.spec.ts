/**
 * Layer 3 — Frontend (Playwright)
 *
 * Requires: docker compose up (all services running)
 * Run: npx playwright test e2e/test_frontend.spec.ts
 *
 * These tests verify the UI correctly shows data that was inserted
 * into the database by the Lambda handler.
 */

import { test, expect, Page } from "@playwright/test";
import { execSync } from "child_process";
import path from "path";

const FRONTEND_URL = process.env.FRONTEND_URL ?? "http://localhost:3000";

// Seed the DB via the Lambda handler before all browser tests
test.beforeAll(async () => {
  const seedScript = path.join(__dirname, "seed_for_playwright.py");
  execSync(`python ${seedScript}`, { stdio: "inherit" });
});

// ─── Reports Table ────────────────────────────────────────────────────────────

test.describe("Reports page", () => {
  test("loads and shows data rows", async ({ page }) => {
    await page.goto(FRONTEND_URL);

    // Wait for table to appear
    const table = page.locator("table");
    await expect(table).toBeVisible({ timeout: 10_000 });

    // At least one row of data should be visible
    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test("shows Finance ministry in the table", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.locator("table").waitFor();

    const cell = page.locator("td", { hasText: "Finance" }).first();
    await expect(cell).toBeVisible();
  });

  test("ministry filter narrows results", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.locator("table").waitFor();

    // Type in the ministry filter
    const input = page.locator('input[placeholder*="ministry"]');
    await input.fill("Health");
    await page.waitForTimeout(500); // debounce

    // All visible rows should show Health
    const cells = page.locator("tbody tr td:first-child");
    for (const cell of await cells.all()) {
      await expect(cell).toHaveText("Health");
    }
  });

  test("fiscal year filter works", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.locator("table").waitFor();

    const input = page.locator('input[placeholder*="Fiscal"]');
    await input.fill("2024-25");
    await page.waitForTimeout(500);

    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCountGreaterThan(0);
  });

  test("amounts are formatted as currency", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.locator("table").waitFor();

    // Amounts should contain a dollar sign
    const amountCells = page.locator("tbody tr td:nth-child(8)");
    const first = amountCells.first();
    await expect(first).toContainText("$");
  });

  test("pagination next button advances page", async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.locator("table").waitFor();

    const nextBtn = page.locator("button", { hasText: "Next" });
    const prevBtn = page.locator("button", { hasText: "Previous" });

    // Previous should be disabled on page 1
    await expect(prevBtn).toBeDisabled();

    // If there is a next page, click it
    const isDisabled = await nextBtn.isDisabled();
    if (!isDisabled) {
      await nextBtn.click();
      await expect(page.locator("text=Page 2")).toBeVisible();
      await expect(prevBtn).toBeEnabled();
    }
  });
});

// ─── Analytics Page ───────────────────────────────────────────────────────────

test.describe("Analytics page", () => {
  async function goToAnalytics(page: Page) {
    await page.goto(FRONTEND_URL);
    await page.locator("a", { hasText: "Analytics" }).click();
    await expect(page).toHaveURL(/analytics/);
  }

  test("shows total spend", async ({ page }) => {
    await goToAnalytics(page);

    const totalSpend = page.locator("text=Total Spend");
    await expect(totalSpend).toBeVisible({ timeout: 10_000 });

    // Should show a dollar value
    const p = page.locator("p", { hasText: "Total Spend" });
    await expect(p).toContainText("$");
  });

  test("renders category pie chart section", async ({ page }) => {
    await goToAnalytics(page);

    const heading = page.locator("h3", { hasText: "Spend by Category" });
    await expect(heading).toBeVisible();

    // Recharts renders an SVG
    const svg = page.locator("section").filter({ hasText: "Spend by Category" }).locator("svg");
    await expect(svg).toBeVisible({ timeout: 10_000 });
  });

  test("renders ministry bar chart section", async ({ page }) => {
    await goToAnalytics(page);

    const heading = page.locator("h3", { hasText: "Spend by Ministry" });
    await expect(heading).toBeVisible();

    const svg = page.locator("section").filter({ hasText: "Spend by Ministry" }).locator("svg");
    await expect(svg).toBeVisible({ timeout: 10_000 });
  });

  test("fiscal year filter re-fetches data", async ({ page }) => {
    await goToAnalytics(page);
    await page.locator("text=Total Spend").waitFor();

    const input = page.locator('input[placeholder*="Fiscal"]');
    await input.fill("2024-25");
    await page.waitForTimeout(600);

    // Charts should still be present after filter
    await expect(page.locator("h3", { hasText: "Spend by Category" })).toBeVisible();
  });
});
