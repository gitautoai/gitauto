# Use Lambda base image with Python 3.13 (Amazon Linux 2023).
FROM public.ecr.aws/lambda/python:3.13

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# Install Python dependencies
# For Amazon Linux 2023-based images (Python 3.13): https://aws.amazon.com/blogs/compute/python-3-13-runtime-now-available-in-aws-lambda/
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN dnf install -y git tar

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