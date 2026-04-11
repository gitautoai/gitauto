import os

AWS_REGION = "us-west-1"

# MongoMemoryServer 7.x misdetects Amazon Linux 2023 as "amazon" (release 2023 > upper bound 3), causing 403 on MongoDB CDN. Versions 9.x+ fixed the detection. Must match the base image in Dockerfile (public.ecr.aws/lambda/python:3.13 = Amazon Linux 2023).
LAMBDA_DISTRO = "amazon2023"

# S3 bucket for dependency tarballs (node_modules.tar.gz, vendor.tar.gz)
S3_DEPENDENCY_BUCKET = os.environ.get(
    "S3_DEPENDENCY_BUCKET", "gitauto-dependency-cache"
)

# 10 minutes - max time to wait for subprocess commands (linters, test runners, etc.)
SUBPROCESS_TIMEOUT_SECONDS = 600
