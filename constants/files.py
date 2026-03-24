JEST_CONFIG_FILES = [
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
]

VITEST_CONFIG_FILES = [
    "vitest.config.ts",
    "vitest.config.js",
    "vitest.config.mts",
    "vitest.config.mjs",
]

JS_TS_FILE_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")

PHP_TEST_FILE_EXTENSIONS = ("Test.php",)

TS_TEST_FILE_EXTENSIONS = (
    ".test.ts",
    ".test.tsx",
    ".spec.ts",
    ".spec.tsx",
)

JS_TEST_FILE_EXTENSIONS = (
    ".test.js",
    ".test.jsx",
    ".spec.js",
    ".spec.jsx",
) + TS_TEST_FILE_EXTENSIONS
