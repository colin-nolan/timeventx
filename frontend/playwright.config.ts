import { defineConfig, devices } from "@playwright/test";

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
    testDir: "./tests",
    /* Run tests in files in parallel */
    fullyParallel: true,
    /* Fail the build on CI if you accidentally left test.only in the source code. */
    forbidOnly: !!process.env.CI,
    /* Retry on CI only */
    retries: process.env.CI ? 2 : 0,
    /* Opt out of parallel tests on CI. */
    workers: process.env.CI ? 1 : undefined,
    /* Reporter to use. See https://playwright.dev/docs/test-reporters */
    reporter: "list",
    /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
    use: {
        /* Base URL to use in actions like `await page.goto('/')`. */
        baseURL: "http://127.0.0.1:3003",

        /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
        trace: "on-first-retry",
    },

    /* Configure projects for major browsers */
    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
        },

        {
            name: "firefox",
            use: { ...devices["Desktop Firefox"] },
        },

        // {
        //     name: "webkit",
        //     use: { ...devices["Desktop Safari"] },
        // },

        /* Test against mobile viewports. */
        // {
        //   name: 'Mobile Chrome',
        //   use: { ...devices['Pixel 5'] },
        // },
        // {
        //   name: 'Mobile Safari',
        //   use: { ...devices['iPhone 12'] },
        // },

        /* Test against branded browsers. */
        // {
        //   name: 'Microsoft Edge',
        //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
        // },
        // {
        //   name: 'Google Chrome',
        //   use: { ...devices['Desktop Chrome'], channel: 'chrome' },
        // },
    ],

    metadata: {
        // FIXME; repeating
        apiServer: "http://127.0.0.1:3004",
    },

    /* Run your local dev server before starting the tests */
    webServer: [
        {
            command: "VITE_BACKEND_API_ROOT=http://127.0.0.1:3004/api/v1 yarn run dev --port 3003",
            url: "http://127.0.0.1:3003",
            reuseExistingServer: !process.env.CI,
        },
        {
            command:
                // FIXME: make temp!
                "GARDEN_WATER_TIMERS_DATABASE_LOCATION=/tmp/test.db " +
                "GARDEN_WATER_BACKEND_PORT=3004 " +
                "GARDEN_WATER_INTERFACE=127.0.0.1 " +
                "GARDEN_WATER_RESTART_ON_ERROR=false " +
                "GARDEN_WATER_LOG_LEVEL=10 " +
                "PYTHONPATH=../backend " +
                "python ../backend/garden_water/main.py",
            url: "http://127.0.0.1:3004/api/v1/healthcheck",
            reuseExistingServer: !process.env.CI,
        },
    ],
});
