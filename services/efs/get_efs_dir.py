import os

from constants.general import IS_PRD

# /mnt/efs on Lambda (prod), /tmp/efs locally
# AWS requires EFS mount path to match /mnt/[a-zA-Z0-9-_.]+
EFS_BASE = "/mnt/efs" if IS_PRD else "/tmp/efs"


def get_efs_dir(owner: str, repo: str):
    return os.path.join(EFS_BASE, owner, repo)
