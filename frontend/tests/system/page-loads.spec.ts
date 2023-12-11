import { test, expect } from "playwright-test-coverage";

test("load index page", async ({ page }) => {
    await page.goto("./");
});

test("load logs page", async ({ page }) => {
    await page.goto("./logs");
});

test("load configuration page", async ({ page }) => {
    await page.goto("./config");
});

test("load stats page", async ({ page }) => {
    await page.goto("./stats");
});

test("load reset page", async ({ page }) => {
    await page.goto("./reset");
});
