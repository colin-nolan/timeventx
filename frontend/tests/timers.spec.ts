import { test, expect } from "playwright-test-coverage";

test.describe.configure({ mode: "serial" });

test("create timer", async ({ page }) => {
    await page.goto("/");
    const originalRowCount = await page.locator(".timerRow").count();

    await page.getByTestId("timer-create-button").click();
    await page.getByTestId("timer-name").fill("example");
    await page.getByTestId("timer-start-time").fill("15:00:00");
    await page.getByTestId("timer-duration").fill("10:00");
    await page.getByTestId("timer-add-button").click();

    expect(page.locator(".timerRow")).toHaveCount(originalRowCount + 1);
});

test("cancel timer creation", async ({ page }) => {
    await page.goto("/");
    const originalRowCount = await page.locator(".timerRow").count();

    await page.getByTestId("timer-create-button").click();
    await page.getByTestId("timer-create-cancel-button").click();
    await page.getByTestId("timer-create-button").click();

    expect(page.locator(".timerRow")).toHaveCount(originalRowCount);
});
