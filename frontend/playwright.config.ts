import { defineConfig, devices } from "@playwright/test";
import { temporaryDirectory } from "tempy";

// XXX: it would be better if these were set to random free ports
const FRONTEND_PORT = 3003;
const BACKEND_PORT = 3004;

const DATABASE_DIRECTORY = temporaryDirectory();
const LOG_LOCATION = `${temporaryDirectory()}/log.txt`;

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
        baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,

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
        apiServer: `http://127.0.0.1:${BACKEND_PORT}`,
    },

    /* Run your local dev server before starting the tests */
    webServer: [
        {
            command: `VITE_BACKEND_API_ROOT=http://127.0.0.1:${BACKEND_PORT}/api/v1 yarn run dev --port ${FRONTEND_PORT}`,
            url: `http://127.0.0.1:${FRONTEND_PORT}`,
            reuseExistingServer: !process.env.CI,
        },
        {
            command:
                `GARDEN_WATER_TIMERS_DATABASE_LOCATION=${DATABASE_DIRECTORY} ` +
                `GARDEN_WATER_LOG_FILE_LOCATION=${LOG_LOCATION} ` +
                `GARDEN_WATER_BACKEND_PORT=${BACKEND_PORT} ` +
                "GARDEN_WATER_INTERFACE=127.0.0.1 " +
                "GARDEN_WATER_RESTART_ON_ERROR=false " +
                "GARDEN_WATER_LOG_LEVEL=10 " +
                "PYTHONPATH=../backend " +
                "python ../backend/garden_water/main.py",
            url: `http://127.0.0.1:${BACKEND_PORT}/api/v1/healthcheck`,
            reuseExistingServer: !process.env.CI,
            // Comment out for logs
            stdout: "ignore",
            stderr: "ignore",
        },
    ],
});
