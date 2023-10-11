import { Page } from "@playwright/test";
import { test, expect } from "playwright-test-coverage";

test.describe.configure({ mode: "serial" });

async function createTimer(page: Page) {
    await page.getByTestId("timer-create-button").click();
    await page.getByTestId("timer-name").fill("example");
    await page.getByTestId("timer-start-time").fill("15:00:00");
    await page.getByTestId("timer-duration").fill("10:00");
    await page.getByTestId("timer-add-button").click();
}

test("create timer", async ({ page }) => {
    await page.goto("/");
    const originalRowCount = await page.locator(".timerRow").count();

    await createTimer(page);

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

test("delete timers", async ({ page }) => {
    await page.goto("/");
    for (let i = 0; i < 3; i++) {
        await createTimer(page);
    }

    const deleteButtons = await page.getByText("Delete");
    const numberOfTimers = await deleteButtons.count();
    for (let i = 0; i < numberOfTimers; i++) {
        await deleteButtons.nth(0).click();
        await page.getByText("Confirm Removal").click();
    }

    expect(page.locator(".timerRow")).toHaveCount(0);
});
