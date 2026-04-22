module.exports = {
  mongodbMemoryServerOptions: {
    binary: {
      version: 'v8.0-latest',
      skipMD5: true,
    },
    instance: {
      dbName: 'jest',
    },
    autoStart: true,
  },
  mongoURLEnvName: 'JEST_MONGODB_URI',
};
