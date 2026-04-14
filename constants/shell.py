# Commands that access the file system — all path arguments must resolve under /tmp
PATH_RESTRICTED_COMMANDS = ("cat", "ls")

# Read-only commands safe to run on Lambda
ALLOWED_PREFIXES = (
    # File system (read-only, paths validated via PATH_RESTRICTED_COMMANDS)
    *[cmd + " " for cmd in PATH_RESTRICTED_COMMANDS],
    # Node/npm
    "node -v",
    "npm list",
    "npm outdated",
    "npm search",
    "npm view",
    # Yarn
    "yarn info",
    "yarn list",
    "yarn why",
    # PHP/Composer
    "composer outdated",
    "composer show",
    "php -m",
    "php -v",
    # Python/pip
    "pip index",
    "pip list",
    "pip show",
)
