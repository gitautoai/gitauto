from services.aws.s3.check_s3_dep_freshness_and_trigger_install import (
    check_s3_dep_freshness_and_trigger_install,
)
from services.aws.s3.get_dep_manifest_hash import get_dep_manifest_hash
from services.python.detect_python_package_manager import detect_python_package_manager
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def ensure_python_packages(
    owner_id: int,
    clone_dir: str,
    owner_name: str,
    repo_name: str,
):
    # Check for Python dependency manifests
    requirements_txt = read_local_file("requirements.txt", base_dir=clone_dir)
    pyproject_toml = read_local_file("pyproject.toml", base_dir=clone_dir)
    pipfile = read_local_file("Pipfile", base_dir=clone_dir)

    if not requirements_txt and not pyproject_toml and not pipfile:
        logger.info(
            "python: No requirements.txt, pyproject.toml, or Pipfile found, skipping"
        )
        return False

    pkg_manager, lock_file_name, lock_file_content = detect_python_package_manager(
        clone_dir
    )

    manifest_files: dict[str, str] = {}
    hash_inputs: list[str | None] = [lock_file_content]

    if requirements_txt:
        manifest_files["requirements.txt"] = requirements_txt
        hash_inputs.append(requirements_txt)

    if pyproject_toml:
        manifest_files["pyproject.toml"] = pyproject_toml
        hash_inputs.append(pyproject_toml)

    if pipfile:
        manifest_files["Pipfile"] = pipfile
        hash_inputs.append(pipfile)

    if lock_file_name and lock_file_content:
        manifest_files[lock_file_name] = lock_file_content

    # Include .python-version for cache invalidation on version changes
    python_version = read_local_file(".python-version", base_dir=clone_dir)
    if python_version:
        manifest_files[".python-version"] = python_version
        hash_inputs.append(python_version)

    manifest_hash = get_dep_manifest_hash(hash_inputs)

    return check_s3_dep_freshness_and_trigger_install(
        owner_name=owner_name,
        repo_name=repo_name,
        owner_id=owner_id,
        pkg_manager=pkg_manager,
        tarball_name="venv.tar.gz",  # Must match SUPPORTED_DEPENDENCY_DIRS in utils/files/is_dependency_file.py
        manifest_hash=manifest_hash,
        manifest_files=manifest_files,
        log_prefix="python",
    )
