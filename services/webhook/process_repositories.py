# Standard imports
import os
from typing import cast

# Local imports
from services.aws.run_install_via_codebuild import run_install_via_codebuild
from services.efs.get_efs_dir import get_efs_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import git_clone_to_efs
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.branches.delete_remote_branch import delete_remote_branch
from services.github.branches.get_default_branch import get_default_branch
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)
from services.github.pulls.create_pull_request import create_pull_request
from services.github.repositories.get_repository_stats import get_repository_stats
from services.github.types.github_types import BaseArgs
from services.github.types.owner import OwnerType
from services.github.types.repository import RepositoryAddedOrRemoved
from services.github.utils.build_setup_pr_body import (
    SETUP_PR_TITLE,
    build_setup_pr_body,
)
from services.node.detect_package_manager import detect_package_manager
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.node.ensure_tsconfig_relaxed_for_tests import (
    ensure_tsconfig_relaxed_for_tests,
)
from services.supabase.repositories.upsert_repository import upsert_repository
from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.generate_branch_name import generate_branch_name
from utils.logging.logging_config import logger, set_owner_repo


@handle_exceptions(raise_on_error=True)
async def process_repositories(
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    repositories: list[RepositoryAddedOrRemoved],
    token: str,
    user_id: int,
    user_name: str,
):
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]
        set_owner_repo(owner_name, repo_name)

        # Insert repository first (without stats to avoid overwriting existing)
        upsert_repository(
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_id=repo_id,
            repo_name=repo_name,
            user_id=user_id,
            user_name=user_name,
        )

        default_branch, is_empty = get_default_branch(
            owner=owner_name, repo=repo_name, token=token
        )

        # Empty repos (size=0) have no commits - skip cloning
        if is_empty:
            logger.info(
                "Repository %s/%s is empty, skipping clone", owner_name, repo_name
            )
            continue

        # Clone or update EFS (reusable for future PR work)
        efs_dir = get_efs_dir(owner_name, repo_name)
        efs_git_dir = os.path.join(efs_dir, ".git")
        clone_url = get_clone_url(owner_name, repo_name, token)

        if os.path.exists(efs_git_dir):
            logger.info("EFS clone exists, updating: %s", efs_dir)
            fetch_ok = await git_fetch(efs_dir, clone_url, default_branch)
            if fetch_ok:
                await git_reset(efs_dir)
        else:
            logger.info("No EFS clone, creating: %s", efs_dir)
            await git_clone_to_efs(efs_dir, clone_url, default_branch)

        # Start package install via CodeBuild (fire-and-forget) for Node projects
        pkg_manager, lock_file, _ = detect_package_manager(efs_dir)
        if lock_file:
            run_install_via_codebuild(efs_dir, owner_id, pkg_manager)

        # Get stats and update repository
        stats = get_repository_stats(local_path=efs_dir)
        logger.info("Repository %s stats: %s", repo_name, stats)
        upsert_repository(
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_id=repo_id,
            repo_name=repo_name,
            user_id=user_id,
            user_name=user_name,
            file_count=stats["file_count"],
            blank_lines=stats["blank_lines"],
            comment_lines=stats["comment_lines"],
            code_lines=stats["code_lines"],
        )

        # Sync files to coverage database
        sync_files_from_github_to_coverage(
            owner=owner_name,
            repo=repo_name,
            branch=default_branch,
            token=token,
            owner_id=owner_id,
            repo_id=repo_id,
            user_name=user_name,
        )

        # Create GitAuto setup PR with any necessary configuration
        new_branch = generate_branch_name(trigger="setup")

        base_args = cast(
            BaseArgs,
            {
                "owner": owner_name,
                "repo": repo_name,
                "token": token,
                "base_branch": default_branch,
                "new_branch": new_branch,
                "clone_dir": efs_dir,
            },
        )

        sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)
        create_remote_branch(sha=sha, base_args=base_args)

        # Run setup tasks - each adds commits if needed
        changes: list[str] = []

        root_files = [
            f for f in os.listdir(efs_dir) if os.path.isfile(os.path.join(efs_dir, f))
        ]

        tsconfig_path, tsconfig_status = ensure_tsconfig_relaxed_for_tests(
            root_files=root_files,
            base_args=base_args,
        )
        if tsconfig_status:
            changes.append(f"{tsconfig_status.capitalize()} {tsconfig_path}")

        if tsconfig_path:
            jest_path, jest_status = ensure_jest_uses_tsconfig_for_tests(
                root_files=root_files,
                base_args=base_args,
                tsconfig_path=tsconfig_path,
            )
            if jest_status:
                changes.append(f"{jest_status.capitalize()} {jest_path}")

        # Future setup tasks can be added here
        # eslint_result = ensure_eslint_config(base_args=base_args, ...)
        # if eslint_result:
        #     changes.append(eslint_result)

        if not changes:
            logger.info("No setup changes needed, deleting branch")
            delete_remote_branch(base_args=base_args)
            continue

        _pr_url, pr_number = create_pull_request(
            body=build_setup_pr_body(changes),
            title=SETUP_PR_TITLE,
            base_args=base_args,
        )

        logger.info("Created setup PR %s/%s#%d", owner_name, repo_name, pr_number)
