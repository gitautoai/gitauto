# Dependency dirs pre-installed on EFS, symlinked (not copied) to tmp clones
DEPENDENCY_DIRS = ["node_modules"]

# 10 minutes - max time to wait for EFS install and run linters
EFS_TIMEOUT_SECONDS = 600

# NAT instance ID for running long tasks via SSM (e.g., yarn linking 872 packages)
# Confirm: aws ec2 describe-instances --filters "Name=tag:Name,Values=gitauto-nat-instance" --query 'Reservations[*].Instances[*].InstanceId' --output text
NAT_INSTANCE_ID = "i-06a54bb6d786a80b5"
