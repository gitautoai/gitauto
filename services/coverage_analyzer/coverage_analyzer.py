# Local imports
from services.coverage_analyzer.dart import parse_lcov_coverage
from services.github.actions_manager import get_workflow_artifacts, download_artifact
from services.github.github_manager import get_installation_access_token
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
    user_name: str,
) -> None:
    token = get_installation_access_token(installation_id=installation_id)

    # Get repository's primary language
    languages = get_repository_languages(owner=owner_name, repo=repo_name, token=token)
    print(f"Languages: {languages}")
    if not languages:
        print("No language information found for repository")
        return

    primary_language = max(languages.items(), key=lambda x: x[1])[0].lower()
    print(f"Primary language: {primary_language}")

    artifacts = get_workflow_artifacts(owner_name, repo_name, run_id, token)
    print(f"Artifacts:\n{artifacts}")

    for artifact in artifacts:
        # Check if the artifact might contain coverage data
        if "coverage" not in artifact["name"].lower():
            print(f"Skipping artifact {artifact['name']} - maybe NOT coverage data")
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

        coverage_data = None
        if primary_language == "dart":
            print("Parsing Dart coverage")
            coverage_data = parse_lcov_coverage(lcov_content)
        elif primary_language in ["javascript", "typescript"]:
            print(f"Coverage parsing not implemented for language: {primary_language}")
            continue
        else:
            print(f"Coverage parsing not implemented for language: {primary_language}")
            continue

        if not coverage_data:
            print(f"No coverage data found for artifact {artifact['name']}")
            continue

        print(f"Saving coverage data for artifact {artifact['name']}")
        create_or_update_coverages(
            coverages_list=coverage_data,
            owner_id=owner_id,
            repo_id=repo_id,
            primary_language=primary_language,
            user_name=user_name,
        )
        print(f"Saved coverage data for artifact {artifact['name']}")
