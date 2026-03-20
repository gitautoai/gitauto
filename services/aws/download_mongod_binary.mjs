/**
 * Pre-downloads the MongoDB binary for MongoMemoryServer so it's cached on EFS.
 * Without this, MongoMemoryServer downloads ~100MB at test runtime, eating into
 * Jest's 600s timeout on Lambda.
 *
 * Called by CodeBuild after `yarn/npm install`, with these env vars:
 *   MONGOMS_DOWNLOAD_DIR - EFS path to cache the binary (e.g. /mnt/efs/owner/repo/.cache/mongodb-binaries)
 *
 * Lambda runs on Amazon Linux 2023. MongoDB < 7.0 has no amazon2023 binary,
 * so we override distro to ubuntu-22.04 (glibc-compatible).
 * MongoDB 7.0+ has native amazon2023 binaries, so auto-detection works.
 *
 * Version detection priority:
 *   1. config.mongodbMemoryServer.version in package.json
 *   2. MONGOMS_VERSION in the test script command (e.g. "cross-env MONGOMS_VERSION=v7.0-latest jest")
 *   3. Library default (if neither is set)
 */

import { readFileSync } from "fs";
import { join } from "path";

const pkg = JSON.parse(readFileSync(join(process.cwd(), "package.json"), "utf8"));

// Check config.mongodbMemoryServer.version first (e.g. {"config": {"mongodbMemoryServer": {"version": "6.0.14"}}})
let version = pkg.config?.mongodbMemoryServer?.version;

// Fall back to extracting MONGOMS_VERSION from the test script command
// e.g. "test": "cross-env MONGOMS_VERSION=v7.0-latest jest --coverage"
if (!version && pkg.scripts) {
  for (const script of Object.values(pkg.scripts)) {
    const match = script.match(/MONGOMS_VERSION=(\S+)/);
    if (match) {
      version = match[1];
      break;
    }
  }
}

console.log("MongoMemoryServer version:", version || "not specified (using library default)");

if (version) {
  process.env.MONGOMS_VERSION = version;
  // Strip leading "v" for major version comparison (e.g. "v7.0-latest" -> "7")
  const major = parseInt(version.replace(/^v/, "").split(".")[0], 10);
  if (major < 7) {
    process.env.MONGOMS_DISTRO = "ubuntu-22.04";
    console.log("Overriding distro to ubuntu-22.04 for MongoDB <7.0 Lambda compatibility");
  }
}

// Dynamic import so version detection runs first (and is testable without this package installed)
const { MongoBinary } = await import("mongodb-memory-server-core");

MongoBinary.getPath()
  .then((p) => console.log("MongoDB binary cached at:", p))
  .catch((e) => {
    console.error("MongoDB binary download failed:", e.message);
    process.exit(1);
  });
