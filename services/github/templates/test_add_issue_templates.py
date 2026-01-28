# pylint: disable=redefined-outer-name
from unittest.mock import Mock, patch

import pytest
from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException, UnknownObjectException
from github.PullRequest import PullRequest
from github.Repository import Repository

from services.github.templates.add_issue_templates import add_issue_templates


@pytest.fixture
def mock_github_setup():
    with patch(
        "services.github.templates.add_issue_templates.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.templates.add_issue_templates.Github"
    ) as mock_github_class, patch(
        "services.github.templates.add_issue_templates.get_latest_remote_commit_sha"
    ) as mock_get_sha, patch(
        "services.github.templates.add_issue_templates.get_file_content"
    ) as mock_get_content, patch(
        "services.github.templates.add_issue_templates.uuid4"
    ) as mock_uuid, patch(
        "services.github.templates.add_issue_templates.PRODUCT_ID", "gitauto"
    ):
        mock_auth = Mock()
        mock_auth_token.return_value = mock_auth

        mock_github = Mock(spec=Github)
        mock_github_class.return_value = mock_github

        mock_repo = Mock(spec=Repository)
        mock_github.get_repo.return_value = mock_repo
        mock_repo.default_branch = "main"
        mock_repo.clone_url = "https://github.com/test-owner/test-repo.git"

        mock_get_sha.return_value = "abc123sha"
        mock_get_content.return_value = "template content"
        mock_uuid.return_value = "test-uuid-1234"

        yield {
            "auth_token": mock_auth_token,
            "auth": mock_auth,
            "github_class": mock_github_class,
            "github": mock_github,
            "repo": mock_repo,
            "get_sha": mock_get_sha,
            "get_content": mock_get_content,
            "uuid": mock_uuid,
        }


def test_success_with_new_templates(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    mocks["auth_token"].assert_called_once_with("test-token")
    mocks["github_class"].assert_called_once_with(auth=mocks["auth"])
    mocks["github"].get_repo.assert_called_once_with(
        full_name_or_id="test-owner/test-repo"
    )

    expected_ref = "refs/heads/gitauto/add-issue-templates-test-uuid-1234"
    mock_repo.create_git_ref.assert_called_once_with(ref=expected_ref, sha="abc123sha")

    assert mock_repo.create_file.call_count == 2

    first_call = mock_repo.create_file.call_args_list[0]
    assert first_call[1]["path"] == ".github/ISSUE_TEMPLATE/bug_report.yml"
    assert first_call[1]["message"] == "Add a template: bug_report.yml"
    assert first_call[1]["content"] == "template content"
    assert first_call[1]["branch"] == "gitauto/add-issue-templates-test-uuid-1234"

    second_call = mock_repo.create_file.call_args_list[1]
    assert second_call[1]["path"] == ".github/ISSUE_TEMPLATE/feature_request.yml"
    assert second_call[1]["message"] == "Add a template: feature_request.yml"
    assert second_call[1]["content"] == "template content"
    assert second_call[1]["branch"] == "gitauto/add-issue-templates-test-uuid-1234"

    mock_repo.create_pull.assert_called_once()
    pr_call = mock_repo.create_pull.call_args
    assert pr_call[1]["base"] == "main"
    assert pr_call[1]["head"] == "gitauto/add-issue-templates-test-uuid-1234"
    assert pr_call[1]["title"] == "Add 2 issue templates"
    assert "bug_report.yml" in pr_call[1]["body"]
    assert "feature_request.yml" in pr_call[1]["body"]
    assert pr_call[1]["maintainer_can_modify"] is True
    assert pr_call[1]["draft"] is False

    mock_pr.create_review_request.assert_called_once_with(reviewers=["installer"])


def test_with_existing_templates(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_existing_file = Mock(spec=ContentFile)
    mock_existing_file.name = "bug_report.yml"
    mock_repo.get_contents.return_value = [mock_existing_file]

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    mock_repo.create_file.assert_called_once()
    call_args = mock_repo.create_file.call_args
    assert call_args[1]["path"] == ".github/ISSUE_TEMPLATE/feature_request.yml"
    assert call_args[1]["message"] == "Add a template: feature_request.yml"

    mock_repo.create_pull.assert_called_once()
    pr_call = mock_repo.create_pull.call_args
    assert pr_call[1]["title"] == "Add 1 issue templates"
    assert "feature_request.yml" in pr_call[1]["body"]
    assert "bug_report.yml" not in pr_call[1]["body"]


def test_all_templates_exist(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_file1 = Mock(spec=ContentFile)
    mock_file1.name = "bug_report.yml"
    mock_file2 = Mock(spec=ContentFile)
    mock_file2.name = "feature_request.yml"
    mock_repo.get_contents.return_value = [mock_file1, mock_file2]

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    mock_repo.create_file.assert_not_called()
    mock_repo.create_pull.assert_not_called()


def test_directory_not_found(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = Exception("Not Found")

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    assert mock_repo.create_file.call_count == 2
    mock_repo.create_pull.assert_called_once()


def test_custom_branch_name(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]
    mock_repo.default_branch = "develop"

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    mock_repo.create_pull.assert_called_once()
    pr_call = mock_repo.create_pull.call_args
    assert pr_call[1]["base"] == "develop"


def test_different_repo_format(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("my-org/my-awesome-repo", "maintainer", "token123")

    assert result is None
    mocks["github"].get_repo.assert_called_once_with(
        full_name_or_id="my-org/my-awesome-repo"
    )

    expected_base_args = {
        "owner": "my-org",
        "repo": "my-awesome-repo",
        "base_branch": "main",
        "token": "token123",
    }
    mocks["get_sha"].assert_called_once_with(
        clone_url="https://github.com/test-owner/test-repo.git",
        base_args=expected_base_args,
    )


@patch(
    "services.github.templates.add_issue_templates.GITHUB_ISSUE_TEMPLATES",
    ["custom_template.yml"],
)
@patch("services.github.templates.add_issue_templates.PRODUCT_ID", "gitauto")
def test_custom_templates(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert result is None
    mock_repo.create_file.assert_called_once()
    call_args = mock_repo.create_file.call_args
    assert call_args[1]["path"] == ".github/ISSUE_TEMPLATE/custom_template.yml"
    assert call_args[1]["message"] == "Add a template: custom_template.yml"

    mock_repo.create_pull.assert_called_once()
    pr_call = mock_repo.create_pull.call_args
    assert pr_call[1]["title"] == "Add 1 issue templates"


def test_handles_exceptions_gracefully():
    with patch(
        "services.github.templates.add_issue_templates.Github"
    ) as mock_github_class:
        mock_github_class.side_effect = Exception("GitHub API error")

        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        assert result is None


def test_uuid_generation(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mocks["uuid"].return_value = "specific-test-uuid"

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    add_issue_templates("test-owner/test-repo", "installer", "test-token")

    mocks["uuid"].assert_called_once()

    expected_ref = "refs/heads/gitauto/add-issue-templates-specific-test-uuid"
    mock_repo.create_git_ref.assert_called_once_with(ref=expected_ref, sha="abc123sha")


def test_file_content_retrieval(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    def mock_get_content_side_effect(file_path):
        if "bug_report.yml" in file_path:
            return "bug report template content"
        if "feature_request.yml" in file_path:
            return "feature request template content"
        return "default content"

    mocks["get_content"].side_effect = mock_get_content_side_effect

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    add_issue_templates("test-owner/test-repo", "installer", "test-token")

    assert mocks["get_content"].call_count == 2

    call_args_list = mocks["get_content"].call_args_list
    expected_paths = [
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
    ]
    actual_paths = [call[1]["file_path"] for call in call_args_list]
    assert set(actual_paths) == set(expected_paths)

    create_file_calls = mock_repo.create_file.call_args_list
    contents = [call[1]["content"] for call in create_file_calls]
    assert "bug report template content" in contents
    assert "feature request template content" in contents


def test_branch_creation_parameters(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mocks["get_sha"].return_value = "specific-sha-123"
    mocks["uuid"].return_value = "branch-uuid"

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    add_issue_templates("test-owner/test-repo", "installer", "test-token")

    expected_base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "base_branch": "main",
        "token": "test-token",
    }
    mocks["get_sha"].assert_called_once_with(
        clone_url="https://github.com/test-owner/test-repo.git",
        base_args=expected_base_args,
    )

    expected_ref = "refs/heads/gitauto/add-issue-templates-branch-uuid"
    mock_repo.create_git_ref.assert_called_once_with(
        ref=expected_ref, sha="specific-sha-123"
    )


def test_pr_body_format(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    add_issue_templates("test-owner/test-repo", "installer", "test-token")

    pr_call = mock_repo.create_pull.call_args
    pr_body = pr_call[1]["body"]

    assert "## Overview" in pr_body
    assert "This PR adds issue templates to the repository" in pr_body
    assert "GitAuto" in pr_body
    assert "## Added templates:" in pr_body
    assert "- bug_report.yml" in pr_body
    assert "- feature_request.yml" in pr_body


def test_decorator_applied():
    assert hasattr(add_issue_templates, "__wrapped__")


def test_return_type_consistency():
    result = add_issue_templates("test-owner/test-repo", "installer", "test-token")
    assert result is None


def test_special_characters_in_repo_name(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates(
        "test-org/repo-with-dashes_and_underscores", "installer", "test-token"
    )

    assert result is None
    mocks["github"].get_repo.assert_called_once_with(
        full_name_or_id="test-org/repo-with-dashes_and_underscores"
    )


def test_empty_installer_name(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    result = add_issue_templates("test-owner/test-repo", "", "test-token")

    assert result is None
    mock_pr.create_review_request.assert_called_once_with(reviewers=[""])


def test_long_repo_name(mock_github_setup):
    mocks = mock_github_setup
    mock_repo = mocks["repo"]

    mock_repo.get_contents.side_effect = UnknownObjectException(
        status=404, data={}, headers={}
    )

    mock_pr = Mock(spec=PullRequest)
    mock_repo.create_pull.return_value = mock_pr

    long_owner = "a" * 100
    long_repo = "b" * 100
    full_name = f"{long_owner}/{long_repo}"

    result = add_issue_templates(full_name, "installer", "test-token")

    assert result is None
    mocks["github"].get_repo.assert_called_once_with(full_name_or_id=full_name)


def test_github_api_error_handling():
    with patch(
        "services.github.templates.add_issue_templates.Github"
    ) as mock_github_class:
        mock_github_class.side_effect = GithubException(status=500, data={}, headers={})

        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        assert result is None


def test_parameter_validation():
    result = add_issue_templates("", "installer", "test-token")
    assert result is None
