# Use Lambda base image
FROM public.ecr.aws/lambda/python:3.12

# Copy to Lambda root(which is specified in Lambda function, usually /var/task/ directory)
COPY . ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN yum install -y patch

# Command to run from Lambda function
CMD ["main.handler"]