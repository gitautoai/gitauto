# Use Lambda base image with Python 3.14 (Amazon Linux 2023).
FROM public.ecr.aws/lambda/python:3.14

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# gcc: needed to build C extensions (e.g. pyiceberg) when no prebuilt 3.14 wheel exists
# git, tar: needed at runtime for cloning repos and extracting archives
RUN dnf install -y gcc git tar

# Install uv (fast Python package manager) and prod-only dependencies
# For Amazon Linux 2023-based images (Python 3.14): https://aws.amazon.com/blogs/compute/python-3-14-runtime-now-available-in-aws-lambda/
# --frozen: use uv.lock exactly, no re-resolution
# --no-dev: skip [dependency-groups].dev packages (linters, test tools, type stubs)
# --no-hashes: skip hash verification (pip freeze didn't have hashes either)
# --target: install into Lambda root, not system Python
# -r -: read requirements from stdin (piped from uv export)
RUN pip install uv && \
    uv export --frozen --no-dev --no-hashes | \
    uv pip install --target "${LAMBDA_TASK_ROOT}" -r -

# Install Node.js (including npm), n (version manager), and yarn
# https://github.com/nodesource/distributions
# Node 22 because express-oauth2-jwt-bearer in foxden-admin-portal-backend requires ≤22.
# FALLBACK_NODE_VERSION env var is read by constants/node.py at runtime.
ARG NODE_VERSION=22
ENV FALLBACK_NODE_VERSION=$NODE_VERSION
RUN curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    dnf install -y nodejs && \
    npm install -g n yarn

# Install PHP CLI and Composer for PHPUnit test execution
# Same packages are also installed in CodeBuild (infrastructure/setup-infra.yml)
# php-cli: PHP command-line interpreter to run PHPUnit
# php-json: JSON encoding/decoding used by PHPUnit for config and result output
# php-mbstring: Multibyte string functions required by PHPUnit for string diffing
# php-xml: DOM/XML parsing used by PHPUnit for phpunit.xml config and JUnit report generation
# php-pdo: Database abstraction layer needed by customer test suites (e.g., SpiderPlus)
RUN dnf install -y php-cli php-json php-mbstring php-xml php-pdo && \
    curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install Playwright's Chromium so customer repos with Playwright/Vitest browser tests can run during verify_task_is_complete (e.g. @vitest/browser-playwright with chromium)
# https://playwright.dev/python/docs/browsers
RUN python -m playwright install chromium

# Command to run from Lambda function
CMD ["main.handler"]