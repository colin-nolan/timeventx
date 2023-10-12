import type { Config } from "jest";

const config: Config = {
    preset: "ts-jest",
    testEnvironment: "node",
    collectCoverage: true,
    testRegex: "tests/unit/.*.ts",
};

export default config;
