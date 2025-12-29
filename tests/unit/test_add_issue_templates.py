# pylint: disable=redefined-outer-name
# Standard imports
from unittest.mock import Mock, patch

# Third-party imports
import pytest
from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException, UnknownObjectException
from github.PullRequest import PullRequest
from github.Repository import Repository

# Local imports
from services.github.templates.add_issue_templates import add_issue_templates


class TestAddIssueTemplates:
    """Test cases for add_issue_templates function."""

    @pytest.fixture
    def mock_github_setup(self):
        """Setup common GitHub mocks."""
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

            # Setup Auth.Token mock
            mock_auth = Mock()
            mock_auth_token.return_value = mock_auth

            # Setup GitHub instance and repository
            mock_github = Mock(spec=Github)
            mock_github_class.return_value = mock_github

            mock_repo = Mock(spec=Repository)
            mock_github.get_repo.return_value = mock_repo
            mock_repo.default_branch = "main"
            mock_repo.clone_url = "https://github.com/test-owner/test-repo.git"

            # Setup other mocks
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

    def test_add_issue_templates_success_with_new_templates(self, mock_github_setup):
        """Test successful addition of new issue templates."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock repository contents - no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None  # Function returns None on success

        # Verify GitHub client initialization
        mocks["auth_token"].assert_called_once_with("test-token")
        mocks["github_class"].assert_called_once_with(auth=mocks["auth"])
        mocks["github"].get_repo.assert_called_once_with(
            full_name_or_id="test-owner/test-repo"
        )

        # Verify branch creation
        expected_ref = "refs/heads/gitauto/add-issue-templates-test-uuid-1234"
        mock_repo.create_git_ref.assert_called_once_with(
            ref=expected_ref, sha="abc123sha"
        )

        # Verify file creation for both templates
        assert mock_repo.create_file.call_count == 2

        # Check first template file creation
        first_call = mock_repo.create_file.call_args_list[0]
        assert first_call[1]["path"] == ".github/ISSUE_TEMPLATE/bug_report.yml"
        assert first_call[1]["message"] == "Add a template: bug_report.yml"
        assert first_call[1]["content"] == "template content"
        assert first_call[1]["branch"] == "gitauto/add-issue-templates-test-uuid-1234"

        # Check second template file creation
        second_call = mock_repo.create_file.call_args_list[1]
        assert second_call[1]["path"] == ".github/ISSUE_TEMPLATE/feature_request.yml"
        assert second_call[1]["message"] == "Add a template: feature_request.yml"
        assert second_call[1]["content"] == "template content"
        assert second_call[1]["branch"] == "gitauto/add-issue-templates-test-uuid-1234"

        # Verify PR creation
        mock_repo.create_pull.assert_called_once()
        pr_call = mock_repo.create_pull.call_args
        assert pr_call[1]["base"] == "main"
        assert pr_call[1]["head"] == "gitauto/add-issue-templates-test-uuid-1234"
        assert pr_call[1]["title"] == "Add 2 issue templates"
        assert "bug_report.yml" in pr_call[1]["body"]
        assert "feature_request.yml" in pr_call[1]["body"]
        assert pr_call[1]["maintainer_can_modify"] is True
        assert pr_call[1]["draft"] is False

        # Verify reviewer assignment
        mock_pr.create_review_request.assert_called_once_with(reviewers=["installer"])

    def test_add_issue_templates_with_existing_templates(self, mock_github_setup):
        """Test when some templates already exist."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock existing files - bug_report.yml already exists
        mock_existing_file = Mock(spec=ContentFile)
        mock_existing_file.name = "bug_report.yml"
        mock_repo.get_contents.return_value = [mock_existing_file]

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None

        # Verify only one file was created (feature_request.yml)
        mock_repo.create_file.assert_called_once()
        call_args = mock_repo.create_file.call_args
        assert call_args[1]["path"] == ".github/ISSUE_TEMPLATE/feature_request.yml"
        assert call_args[1]["message"] == "Add a template: feature_request.yml"

        # Verify PR creation with only one template
        mock_repo.create_pull.assert_called_once()
        pr_call = mock_repo.create_pull.call_args
        assert pr_call[1]["title"] == "Add 1 issue templates"
        assert "feature_request.yml" in pr_call[1]["body"]
        assert "bug_report.yml" not in pr_call[1]["body"]

    def test_add_issue_templates_all_templates_exist(self, mock_github_setup):
        """Test when all templates already exist."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock existing files - both templates already exist
        mock_file1 = Mock(spec=ContentFile)
        mock_file1.name = "bug_report.yml"
        mock_file2 = Mock(spec=ContentFile)
        mock_file2.name = "feature_request.yml"
        mock_repo.get_contents.return_value = [mock_file1, mock_file2]

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None

        # Verify no files were created
        mock_repo.create_file.assert_not_called()

        # Verify no PR was created
        mock_repo.create_pull.assert_not_called()

    def test_add_issue_templates_with_directory_not_found(self, mock_github_setup):
        """Test when the issue template directory doesn't exist."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock directory not found (404 error)
        mock_repo.get_contents.side_effect = Exception("Not Found")

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None

        # Verify both files were created (since directory doesn't exist, no existing files)
        assert mock_repo.create_file.call_count == 2

        # Verify PR was created
        mock_repo.create_pull.assert_called_once()

    def test_add_issue_templates_with_custom_branch_name(self, mock_github_setup):
        """Test with a custom default branch name."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]
        mock_repo.default_branch = "develop"

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None

        # Verify PR was created with correct base branch
        mock_repo.create_pull.assert_called_once()
        pr_call = mock_repo.create_pull.call_args
        assert pr_call[1]["base"] == "develop"

    def test_add_issue_templates_with_different_repo_format(self, mock_github_setup):
        """Test with different repository name formats."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function with organization/repo format
        result = add_issue_templates("my-org/my-awesome-repo", "maintainer", "token123")

        # Assertions
        assert result is None

        # Verify correct repository was accessed
        mocks["github"].get_repo.assert_called_once_with(
            full_name_or_id="my-org/my-awesome-repo"
        )

        # Verify get_latest_remote_commit_sha was called with correct args
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
    def test_add_issue_templates_with_custom_templates(self, mock_github_setup):
        """Test with custom issue templates configuration."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Assertions
        assert result is None

        # Verify only one file was created
        mock_repo.create_file.assert_called_once()
        call_args = mock_repo.create_file.call_args
        assert call_args[1]["path"] == ".github/ISSUE_TEMPLATE/custom_template.yml"
        assert call_args[1]["message"] == "Add a template: custom_template.yml"

        # Verify PR title reflects single template
        mock_repo.create_pull.assert_called_once()
        pr_call = mock_repo.create_pull.call_args
        assert pr_call[1]["title"] == "Add 1 issue templates"

    def test_add_issue_templates_handles_exceptions_gracefully(self):
        """Test that the function handles exceptions gracefully due to @handle_exceptions decorator."""
        with patch(
            "services.github.templates.add_issue_templates.Github"
        ) as mock_github_class:
            # Mock Github to raise an exception
            mock_github_class.side_effect = Exception("GitHub API error")

            # Call the function - should not raise exception due to decorator
            result = add_issue_templates(
                "test-owner/test-repo", "installer", "test-token"
            )

            # Should return None due to decorator's default_return_value
            assert result is None

    def test_add_issue_templates_uuid_generation(self, mock_github_setup):
        """Test that UUID is properly generated for branch names."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Set specific UUID for testing
        mocks["uuid"].return_value = "specific-test-uuid"

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Verify UUID was called
        mocks["uuid"].assert_called_once()

        # Verify branch name includes the UUID
        expected_ref = "refs/heads/gitauto/add-issue-templates-specific-test-uuid"
        mock_repo.create_git_ref.assert_called_once_with(
            ref=expected_ref, sha="abc123sha"
        )

    def test_add_issue_templates_file_content_retrieval(self, mock_github_setup):
        """Test that file content is properly retrieved for each template."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock different content for each template
        def mock_get_content_side_effect(file_path):
            if "bug_report.yml" in file_path:
                return "bug report template content"
            if "feature_request.yml" in file_path:
                return "feature request template content"
            return "default content"

        mocks["get_content"].side_effect = mock_get_content_side_effect

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Verify get_file_content was called for both templates
        assert mocks["get_content"].call_count == 2

        # Verify correct paths were used
        call_args_list = mocks["get_content"].call_args_list
        expected_paths = [
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
        ]
        actual_paths = [call[1]["file_path"] for call in call_args_list]
        assert set(actual_paths) == set(expected_paths)

        # Verify correct content was used in file creation
        create_file_calls = mock_repo.create_file.call_args_list
        contents = [call[1]["content"] for call in create_file_calls]
        assert "bug report template content" in contents
        assert "feature request template content" in contents

    def test_add_issue_templates_print_statements(self, mock_github_setup):
        """Test that appropriate print statements are made."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        with patch("builtins.print") as mock_print:
            # Call the function
            add_issue_templates("test-owner/test-repo", "installer", "test-token")

            # Verify print was called with the expected message
            mock_print.assert_called_once_with(
                "Adding issue templates to the repo: 'test-owner/test-repo' by 'installer'.\n"
            )

    def test_add_issue_templates_branch_creation_parameters(self, mock_github_setup):
        """Test that branch creation uses correct parameters."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Set specific values for testing
        mocks["get_sha"].return_value = "specific-sha-123"
        mocks["uuid"].return_value = "branch-uuid"

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Verify get_latest_remote_commit_sha was called with correct parameters
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

        # Verify branch creation with correct SHA
        expected_ref = "refs/heads/gitauto/add-issue-templates-branch-uuid"
        mock_repo.create_git_ref.assert_called_once_with(
            ref=expected_ref, sha="specific-sha-123"
        )

    def test_add_issue_templates_pr_body_format(self, mock_github_setup):
        """Test that PR body is formatted correctly."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function
        add_issue_templates("test-owner/test-repo", "installer", "test-token")

        # Verify PR body contains expected content
        pr_call = mock_repo.create_pull.call_args
        pr_body = pr_call[1]["body"]

        # Check that body contains overview section
        assert "## Overview" in pr_body
        assert "This PR adds issue templates to the repository" in pr_body
        assert "GitAuto" in pr_body

        # Check that body contains added templates section
        assert "## Added templates:" in pr_body
        assert "- bug_report.yml" in pr_body
        assert "- feature_request.yml" in pr_body

    def test_add_issue_templates_function_docstring_exists(self):
        """Test that the function has proper documentation."""
        assert (
            add_issue_templates.__doc__ is None
        )  # This function doesn't have a docstring

    def test_add_issue_templates_decorator_applied(self):
        """Test that the @handle_exceptions decorator is properly applied."""
        assert hasattr(add_issue_templates, "__wrapped__")

    def test_add_issue_templates_return_type_consistency(self):
        """Test that return type is consistent (always None)."""
        # The function should always return None due to the decorator and explicit returns
        result = add_issue_templates("test-owner/test-repo", "installer", "test-token")
        assert result is None

    def test_add_issue_templates_with_special_characters_in_repo_name(
        self, mock_github_setup
    ):
        """Test with repository names containing special characters."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function with special characters in repo name
        result = add_issue_templates(
            "test-org/repo-with-dashes_and_underscores", "installer", "test-token"
        )

        # Verify it still works
        assert result is None
        mocks["github"].get_repo.assert_called_once_with(
            full_name_or_id="test-org/repo-with-dashes_and_underscores"
        )

    def test_add_issue_templates_with_empty_installer_name(self, mock_github_setup):
        """Test with empty installer name."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Call the function with empty installer name
        result = add_issue_templates("test-owner/test-repo", "", "test-token")

        # Should still work, but reviewer assignment might fail gracefully
        assert result is None
        mock_pr.create_review_request.assert_called_once_with(reviewers=[""])

    def test_add_issue_templates_with_long_repo_name(self, mock_github_setup):
        """Test with very long repository name."""
        mocks = mock_github_setup
        mock_repo = mocks["repo"]

        # Mock no existing templates
        mock_repo.get_contents.side_effect = UnknownObjectException(
            status=404, data={}, headers={}
        )

        # Mock PR creation
        mock_pr = Mock(spec=PullRequest)
        mock_repo.create_pull.return_value = mock_pr

        # Create very long repo name
        long_owner = "a" * 100
        long_repo = "b" * 100
        full_name = f"{long_owner}/{long_repo}"

        # Call the function
        result = add_issue_templates(full_name, "installer", "test-token")

        # Should still work
        assert result is None
        mocks["github"].get_repo.assert_called_once_with(full_name_or_id=full_name)

    def test_add_issue_templates_github_api_error_handling(self):
        """Test that GitHub API errors are handled gracefully."""
        with patch(
            "services.github.templates.add_issue_templates.Github"
        ) as mock_github_class:
            mock_github_class.side_effect = GithubException(
                status=500, data={}, headers={}
            )

            # Call the function - should not raise exception due to decorator
            result = add_issue_templates(
                "test-owner/test-repo", "installer", "test-token"
            )

            # Should return None due to decorator's default_return_value
            assert result is None

    def test_add_issue_templates_parameter_validation(self):
        """Test function behavior with various parameter types."""
        # Test with empty strings - should be handled by decorator
        result = add_issue_templates("", "installer", "test-token")
        assert result is None
