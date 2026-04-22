# Default MongoDB server versions that mongodb-memory-server downloads when no version is specified in package.json config.
# Must match upstream so GA tests against the same MongoDB the customer's CI does.
# https://github.com/typegoose/mongodb-memory-server/blob/master/packages/mongodb-memory-server-core/src/util/resolve-config.ts
MONGOMS_MAJOR_TO_MONGODB_VERSION: dict[int, str] = {
    7: "6.0.9",
    8: "6.0.9",
    9: "6.0.9",
    10: "7.0.11",
    11: "8.2.1",
}
