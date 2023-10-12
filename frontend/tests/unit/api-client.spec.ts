import { ApiClient } from "../../src/lib/api-client";
import { env } from "process";
import { test, expect, describe } from "@jest/globals";

function createClient() {
    const apiServerRoot = `${env.BACKEND_URL}/api/v1`;
    return new ApiClient(apiServerRoot);
}

test("get stats", async () => {
    const client = createClient();
    // Expecting because not implemented outside of rp2040
    await expect(client.getStats()).rejects.toBeDefined();
});

test("get logs", async () => {
    const client = createClient();
    await expect(client.getLogs()).toBeDefined();
});

test("clear logs", async () => {
    const client = createClient();
    await client.clearLogs();
});

test("reset device", async () => {
    const client = createClient();
    // Expecting because not implemented outside of rp2040
    await expect(client.resetDevice()).rejects.toBeDefined();
});

test("get intervals", async () => {
    const client = createClient();

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

describe("TimersClient", () => {
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

    test("add or update timer", async () => {
        const client = createClient();

        await client.timers.addOrUpdateTimer(EXAMPLE_TIMER_WITH_ID_1);
        const timers1 = await client.timers.getTimers();
        expect(timers1).toContainEqual(EXAMPLE_TIMER_WITH_ID_1);

        await client.timers.addOrUpdateTimer(EXAMPLE_TIMER_WITH_ID_1);
        const timers2 = await client.timers.getTimers();
        expect(timers2).toContainEqual(EXAMPLE_TIMER_WITH_ID_1);
    });

    test("add timer", async () => {
        const client = createClient();

        await client.timers.addTimer(EXAMPLE_TIMER_1);

        expect(await client.timers.getTimers()).toContainEqual(expect.objectContaining(EXAMPLE_TIMER_1));
    });

    test("update timer", async () => {
        const client = createClient();

        const timer1 = await client.timers.addTimer(EXAMPLE_TIMER_1);
        await client.timers.updateTimer({ ...EXAMPLE_TIMER_2, id: timer1.id });

        const timers = await client.timers.getTimers();
        expect(timers).toContainEqual({ ...EXAMPLE_TIMER_2, id: timer1.id });
        expect(timers).not.toContainEqual(timer1);
    });

    test("remove timer", async () => {
        const client = createClient();

        const timer = await client.timers.addTimer(EXAMPLE_TIMER_1);
        await client.timers.removeTimer(timer.id);

        expect(await client.timers.getTimers()).not.toContainEqual(timer);
    });
});
