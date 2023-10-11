import { test, expect } from "playwright-test-coverage";
import { ApiClient, Timer } from "../../src/lib/api-client";
import { TestInfo } from "@playwright/test";
import { ExpandOutlined } from "@mui/icons-material";

function createClient(testInfo: TestInfo) {
    const apiServerRoot = `${testInfo.config.metadata["apiServer"]}/api/v1`;
    return new ApiClient(apiServerRoot);
}

test("get stats", async ({}, testInfo) => {
    const client = createClient(testInfo);
    // Expecting because not implemented outside of rp2040
    await expect(client.getStats()).rejects.toBeDefined();
});

test("get logs", async ({}, testInfo) => {
    const client = createClient(testInfo);
    await expect(await client.getLogs()).toBeDefined();
});

test("clear logs", async ({}, testInfo) => {
    const client = createClient(testInfo);
    await client.clearLogs();
});

test("reset device", async ({}, testInfo) => {
    const client = createClient(testInfo);
    // Expecting because not implemented outside of rp2040
    await expect(client.resetDevice()).rejects.toBeDefined();
});

test("get intervals", async ({}, testInfo) => {
    const client = createClient(testInfo);

    await client.timers.addTimer({
        name: "example1",
        startTime: "10:00:00",
        duration: 65,
    });
    await client.timers.addTimer({
        name: "example2",
        startTime: "10:01:00",
        duration: 10,
    });

    const intervals = await client.getIntervals();
    expect(intervals).toContainEqual({ startTime: "10:00:00", endTime: "10:01:10" });
});

test.describe("TimersClient", () => {
    const EXAMPLE_TIMER_1 = {
        name: "example1",
        startTime: "01:02:03",
        duration: 60,
    };
    const EXAMPLE_TIMER_2 = {
        name: "example2",
        startTime: "03:02:01",
        duration: 180,
    };
    const EXAMPLE_TIMER_WITH_ID_1 = {
        ...EXAMPLE_TIMER_1,
        id: Math.floor(Math.random() * 999999999),
    };

    test("add or update timer", async ({}, testInfo) => {
        const client = createClient(testInfo);

        await client.timers.addOrUpdateTimer(EXAMPLE_TIMER_WITH_ID_1);
        const timers1 = await client.timers.getTimers();
        expect(timers1).toContainEqual(EXAMPLE_TIMER_WITH_ID_1);

        await client.timers.addOrUpdateTimer(EXAMPLE_TIMER_WITH_ID_1);
        const timers2 = await client.timers.getTimers();
        expect(timers2).toContainEqual(EXAMPLE_TIMER_WITH_ID_1);
    });

    test("add timer", async ({}, testInfo) => {
        const client = createClient(testInfo);

        await client.timers.addTimer(EXAMPLE_TIMER_1);

        expect(await client.timers.getTimers()).toContainEqual(expect.objectContaining(EXAMPLE_TIMER_1));
    });

    test("update timer", async ({}, testInfo) => {
        const client = createClient(testInfo);

        const timer1 = await client.timers.addTimer(EXAMPLE_TIMER_1);
        await client.timers.updateTimer({ ...EXAMPLE_TIMER_2, id: timer1.id });

        const timers = await client.timers.getTimers();
        expect(timers).toContainEqual({ ...EXAMPLE_TIMER_2, id: timer1.id });
        expect(timers).not.toContainEqual(timer1);
    });

    test("remove timer", async ({}, testInfo) => {
        const client = createClient(testInfo);

        const timer = await client.timers.addTimer(EXAMPLE_TIMER_1);
        await client.timers.removeTimer(timer.id);

        expect(await client.timers.getTimers()).not.toContainEqual(timer);
    });
});
