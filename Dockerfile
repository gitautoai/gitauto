# Use Lambda base image with Python 3.13
FROM public.ecr.aws/lambda/python:3.13

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# Install Python dependencies
# For Amazon Linux 2023-based images (Python 3.13): https://aws.amazon.com/blogs/compute/python-3-13-runtime-now-available-in-aws-lambda/
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN dnf install -y git tar

# Install Node.js (including npm) and yarn
# https://github.com/nodesource/distributions
RUN curl -fsSL https://rpm.nodesource.com/setup_24.x | bash - && \
    dnf install -y nodejs && \
    npm install -g yarn

# Install PHP CLI and Composer for PHPUnit test execution
# Same packages are also installed in CodeBuild (infrastructure/setup-vpc-nat-s3.yml)
# php-cli: PHP command-line interpreter to run PHPUnit
# php-json: JSON encoding/decoding used by PHPUnit for config and result output
# php-mbstring: Multibyte string functions required by PHPUnit for string diffing
# php-xml: DOM/XML parsing used by PHPUnit for phpunit.xml config and JUnit report generation
# php-pdo: Database abstraction layer needed by customer test suites (e.g., SpiderPlus)
RUN dnf install -y php-cli php-json php-mbstring php-xml php-pdo && \
    curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install cloc directly without adding the entire EPEL repository
RUN curl -L https://github.com/AlDanial/cloc/releases/download/v1.98/cloc-1.98.pl -o /usr/local/bin/cloc && \
    chmod +x /usr/local/bin/cloc

# Install Playwright's browser without dependencies (install-deps)
# https://playwright.dev/python/docs/browsers
RUN python -m playwright install chromium

# Command to run from Lambda function
CMD ["main.handler"]