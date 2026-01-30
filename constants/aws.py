AWS_REGION = "us-west-1"

# Dependency dirs pre-installed on EFS, symlinked (not copied) to tmp clones
DEPENDENCY_DIRS = ["node_modules"]

# 10 minutes - max time to wait for EFS install and run linters
EFS_TIMEOUT_SECONDS = 600
