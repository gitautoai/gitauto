# Use Lambda base image with Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# Install Python dependencies
# For Amazon Linux 2023-based images (Python 3.12): https://aws.amazon.com/blogs/compute/python-3-12-runtime-now-available-in-aws-lambda/
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN dnf install -y patch git

# Install Node.js (including npm) and yarn
# https://github.com/nodesource/distributions
RUN curl -fsSL https://rpm.nodesource.com/setup_lts.x | bash - && \
    dnf install -y nodejs && \
    npm install -g yarn

# Install cloc directly without adding the entire EPEL repository
RUN curl -L https://github.com/AlDanial/cloc/releases/download/v1.98/cloc-1.98.pl -o /usr/local/bin/cloc && \
    chmod +x /usr/local/bin/cloc

# Install Playwright's browser without dependencies (install-deps)
# https://playwright.dev/python/docs/browsers
RUN python -m playwright install chromium

# Command to run from Lambda function
CMD ["main.handler"]