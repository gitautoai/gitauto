# Use Lambda base image
FROM public.ecr.aws/lambda/python:3.12

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# Install dependencies
# For Amazon Linux 2023-based images (Python 3.12): https://aws.amazon.com/blogs/compute/python-3-12-runtime-now-available-in-aws-lambda/
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN dnf install -y patch git

# Command to run from Lambda function
CMD ["main.handler"]