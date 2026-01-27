#!/bin/bash
# Check for built-in logging imports - use utils.logging.logging_config instead
# Exit 0 if no issues, exit 1 if bad imports found
matches=$(grep -r "^import logging$" --include="*.py" . --exclude-dir=venv | grep -v "utils/logging/logging_config.py")
if [ -n "$matches" ]; then
    echo "$matches"
    exit 1
fi
exit 0
