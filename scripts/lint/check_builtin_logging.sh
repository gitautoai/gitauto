#!/bin/bash
# Check for built-in logging imports - use utils.logging.logging_config instead
grep -r "^import logging$" --include="*.py" . --exclude-dir=venv | grep -v "utils/logging/logging_config.py"
