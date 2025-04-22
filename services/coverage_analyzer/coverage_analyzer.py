# Local imports
from services.coverage_analyzer.lcov import parse_lcov_coverage
from services.github.actions_manager import get_workflow_artifacts, download_artifact
from services.github.github_manager import (
    get_installation_access_token,
    get_remote_file_tree,
)
from services.github.repo_manager import get_repository_languages
from services.supabase.coverage_manager import create_or_update_coverages
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_workflow_coverage(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    run_id: int,
    head_branch: str,
    user_name: str,
):
    token = get_installation_access_token(installation_id=installation_id)

    # Get repository's primary language
    languages = get_repository_languages(owner=owner_name, repo=repo_name, token=token)
    if not languages:
        print("No language information found for repository")
        return

    primary_language = max(languages.items(), key=lambda x: x[1])[0].lower()

    artifacts = get_workflow_artifacts(owner_name, repo_name, run_id, token)

    coverage_data = []
    for artifact in artifacts:
        # Check if the artifact might contain coverage data
        if "coverage" not in artifact["name"].lower():
            continue

        # Download and parse lcov.info
        print(f"Downloading artifact {artifact['name']}")
        lcov_content = download_artifact(
            owner=owner_name, repo=repo_name, artifact_id=artifact["id"], token=token
        )
        print(f"Downloaded artifact {artifact['name']}")

        if lcov_content is None:
            print(f"No lcov.info found in artifact {artifact['name']}")
            continue

        supported_languages = ["javascript", "typescript", "python", "dart"]
        if primary_language not in supported_languages:
            print(f"Coverage parsing not implemented for language: {primary_language}")
            continue

        print(f"Parsing {primary_language} coverage")
        parsed_coverage = parse_lcov_coverage(lcov_content)

        if parsed_coverage:
            coverage_data.extend(parsed_coverage)

    if coverage_data:
        # Add uncovered files for all supported languages
        base_args = {
            "owner": owner_name,
            "repo": repo_name,
            "token": token,
            "base_branch": head_branch,
        }

        # Get all source files from the repository
        all_files, _ = get_remote_file_tree(base_args=base_args)

        # Filter files based on language extension
        extension_map = {
            "javascript": ".js",
            "typescript": ".ts",
            "python": ".py",
            "dart": ".dart",
        }

        source_files = [
            f for f in all_files if f.endswith(extension_map.get(primary_language, ""))
        ]

        # Get files that are already in coverage report
        covered_files = {
            report["full_path"] for report in coverage_data if report["level"] == "file"
        }

        # Add uncovered files with 0% coverage
        for source_file in source_files:
            # Skip test files based on language conventions
            test_patterns = {
                "javascript": ["test.js", "spec.js", "__tests__"],
                "typescript": ["test.ts", "spec.ts", "__tests__"],
                "python": ["test_", "_test.py", "tests/"],
                "dart": ["test.dart", "_test.dart", "test/"],
            }

            patterns = test_patterns.get(primary_language, [])
            if any(pattern in source_file for pattern in patterns):
                continue

            if source_file not in covered_files:
                coverage_data.append(
                    {
                        "package_name": None,
                        "level": "file",
                        "full_path": source_file,
                        "statement_coverage": 0.0,
                        "function_coverage": 0.0,
                        "branch_coverage": 0.0,
                        "line_coverage": 0.0,
                        "uncovered_lines": "",
                        "uncovered_functions": "",
                        "uncovered_branches": "",
                    }
                )

    if coverage_data:
        print("Saving coverage data")
        create_or_update_coverages(
            coverages_list=coverage_data,
            owner_id=owner_id,
            repo_id=repo_id,
            branch_name=head_branch,
            primary_language=primary_language,
            user_name=user_name,
        )
        print("Saved coverage data")
