import os
import subprocess

from botocore.exceptions import ClientError

from constants.aws import S3_DEPENDENCY_BUCKET
from services.aws.clients import s3_client
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_dependency_file import SUPPORTED_DEPENDENCY_DIRS
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def download_and_extract_s3_deps(
    *,
    owner_name: str,
    repo_name: str,
    clone_dir: str,
):
    """Download cached dependency tarballs from S3 and extract to clone_dir."""
    for dep_dir in SUPPORTED_DEPENDENCY_DIRS:
        target_path = os.path.join(clone_dir, dep_dir)
        if os.path.exists(target_path):
            logger.info(
                "S3 extract skip: %s already exists at %s", dep_dir, target_path
            )
            continue

        s3_key = f"{owner_name}/{repo_name}/{dep_dir}.tar.gz"
        local_tarball = os.path.join(clone_dir, f"{dep_dir}.tar.gz")

        # 404 is expected (e.g. Node repo has no vendor.tar.gz), skip and continue loop
        try:
            s3_client.download_file(
                Bucket=S3_DEPENDENCY_BUCKET,
                Key=s3_key,
                Filename=local_tarball,
            )
        except ClientError as e:
            error_info = e.response.get("Error")
            error_code = error_info.get("Code") if error_info else None
            if error_code in ("404", "NoSuchKey"):
                logger.info(
                    "S3 extract skip: no tarball at s3://%s/%s",
                    S3_DEPENDENCY_BUCKET,
                    s3_key,
                )
                continue
            raise

        logger.info("Extracting %s from S3 tarball...", dep_dir)
        subprocess.run(
            # x=extract, z=gzip, f=file, C=target dir
            ["tar", "-xzf", local_tarball, "-C", clone_dir],
            check=True,
            capture_output=True,
        )
        os.remove(local_tarball)
        logger.info(
            "Extracted: s3://%s/%s -> %s", S3_DEPENDENCY_BUCKET, s3_key, target_path
        )
