/**
 * Tests for download_mongod_binary.mjs version detection logic.
 * Run with: node --test services/aws/download_mongod_binary.test.mjs
 *
 * These tests verify version extraction from real customer package.json configs
 * WITHOUT requiring mongodb-memory-server-core to be installed.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { execFileSync } from "child_process";

/**
 * Runs the download script against a mock package.json in a temp dir.
 * The script will fail on the dynamic import("mongodb-memory-server-core") since it's
 * not installed locally, but version detection runs before that and is visible in output.
 */
function runWithPackageJson(pkg) {
  const tmpDir = join("/tmp", `mongod-test-${Date.now()}`);
  mkdirSync(tmpDir, { recursive: true });
  writeFileSync(join(tmpDir, "package.json"), JSON.stringify(pkg));

  try {
    const output = execFileSync(
      "node",
      [join(process.cwd(), "services/aws/download_mongod_binary.mjs")],
      { cwd: tmpDir, encoding: "utf8", env: { ...process.env, MONGOMS_DOWNLOAD_DIR: "/tmp/mongod-test-cache" }, timeout: 5000 },
    );
    return { output, exitCode: 0 };
  } catch (e) {
    return { output: (e.stdout || "") + (e.stderr || ""), exitCode: e.status };
  } finally {
    rmSync(tmpDir, { recursive: true, force: true });
  }
}

describe("download_mongod_binary", () => {
  // Real case: Foxquilt/foxcom-payment-backend
  // - mongodb-memory-server ^7.4.0 in dependencies
  // - MONGOMS_VERSION=v7.0-latest via cross-env in test script
  it("foxcom-payment-backend: cross-env MONGOMS_VERSION in test script", () => {
    const { output } = runWithPackageJson({
      name: "foxcom-payment-backend",
      scripts: {
        test: 'cross-env MONGOMS_VERSION=v7.0-latest jest --coverage --coverageReporters="lcov"',
      },
      dependencies: { "mongodb-memory-server": "^7.4.0" },
    });
    assert.match(output, /MongoMemoryServer version: v7\.0-latest/);
    assert.doesNotMatch(output, /ubuntu-22\.04/, "v7.0 should NOT override distro");
  });

  // Real case: Foxquilt/foxcom-forms-backend
  // - mongodb-memory-server 7.4.0 (exact, not caret) in dependencies
  // - MONGOMS_VERSION=v7.0-latest directly (no cross-env prefix)
  it("foxcom-forms-backend: MONGOMS_VERSION without cross-env", () => {
    const { output } = runWithPackageJson({
      name: "foxcom-forms-backend",
      scripts: {
        test: "MONGOMS_VERSION=v7.0-latest NODE_OPTIONS='--max-old-space-size=6144' jest",
      },
      dependencies: { "mongodb-memory-server": "7.4.0" },
    });
    assert.match(output, /MongoMemoryServer version: v7\.0-latest/);
    assert.doesNotMatch(output, /ubuntu-22\.04/);
  });

  // Real case: Foxquilt/foxden-rating-quoting-backend
  // - mongodb-memory-server 9.1.5 in dependencies
  // - TZ=UTC before MONGOMS_VERSION in test script
  it("foxden-rating-quoting-backend: TZ=UTC before MONGOMS_VERSION", () => {
    const { output } = runWithPackageJson({
      name: "foxden-rating-quoting-backend",
      scripts: {
        test: "cross-env TZ=UTC MONGOMS_VERSION=v7.0-latest NODE_OPTIONS='--max-old-space-size=6144' jest",
      },
      dependencies: { "mongodb-memory-server": "9.1.5" },
    });
    assert.match(output, /MongoMemoryServer version: v7\.0-latest/);
    assert.doesNotMatch(output, /ubuntu-22\.04/);
  });

  // Real case: Foxquilt/foxden-tools
  // - mongodb-memory-server ^9.1.7 in dependencies
  // - yarn build && before cross-env MONGOMS_VERSION in test script
  it("foxden-tools: yarn build && before MONGOMS_VERSION", () => {
    const { output } = runWithPackageJson({
      name: "foxden-tools",
      scripts: {
        test: "yarn build && cross-env MONGOMS_VERSION=v7.0-latest jest",
      },
      dependencies: { "mongodb-memory-server": "^9.1.7" },
    });
    assert.match(output, /MongoMemoryServer version: v7\.0-latest/);
    assert.doesNotMatch(output, /ubuntu-22\.04/);
  });

  // Real case: Foxquilt/foxden-billing
  // - mongodb-memory-server ^10.0.0 in dependencies
  // - NO MONGOMS_VERSION in any script, no config section
  it("foxden-billing: no version specified anywhere", () => {
    const { output } = runWithPackageJson({
      name: "foxden-billing",
      scripts: { test: "jest" },
      dependencies: { "mongodb-memory-server": "^10.0.0" },
    });
    assert.match(output, /not specified \(using library default\)/);
    assert.doesNotMatch(output, /ubuntu-22\.04/);
  });

  // Real case: Foxquilt/foxden-shared-lib
  // - mongodb-memory-server ^9.3.0 in dependencies
  // - NO MONGOMS_VERSION in any script, no config section
  it("foxden-shared-lib: no version specified anywhere", () => {
    const { output } = runWithPackageJson({
      name: "foxden-shared-lib",
      dependencies: { "mongodb-memory-server": "^9.3.0" },
    });
    assert.match(output, /not specified \(using library default\)/);
    assert.doesNotMatch(output, /ubuntu-22\.04/);
  });

  // Hypothetical case: older MongoDB version in config section
  // - config.mongodbMemoryServer.version = "6.0.14"
  // - Should override distro to ubuntu-22.04 for Lambda compatibility
  it("config section with MongoDB <7 overrides distro", () => {
    const { output } = runWithPackageJson({
      name: "test-repo",
      config: { mongodbMemoryServer: { version: "6.0.14" } },
      dependencies: { "mongodb-memory-server": "^9.0.0" },
    });
    assert.match(output, /MongoMemoryServer version: 6\.0\.14/);
    assert.match(output, /ubuntu-22\.04/);
  });

  // config.mongodbMemoryServer.version takes priority over script env var
  it("config section takes priority over test script env var", () => {
    const { output } = runWithPackageJson({
      name: "test-repo",
      config: { mongodbMemoryServer: { version: "6.0.14" } },
      scripts: { test: "cross-env MONGOMS_VERSION=v7.0-latest jest" },
      dependencies: { "mongodb-memory-server": "^9.0.0" },
    });
    assert.match(output, /MongoMemoryServer version: 6\.0\.14/);
  });
});
