import os

AWS_REGION = "us-west-1"

# S3 bucket for dependency tarballs (node_modules.tar.gz, vendor.tar.gz)
S3_DEPENDENCY_BUCKET = os.environ.get(
    "S3_DEPENDENCY_BUCKET", "gitauto-dependency-cache"
)

# 10 minutes - max time to wait for EFS install and run linters
EFS_TIMEOUT_SECONDS = 600
