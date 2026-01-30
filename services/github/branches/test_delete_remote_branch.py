# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import MagicMock, patch

from services.github.branches.delete_remote_branch import delete_remote_branch
from services.github.types.github_types import BaseArgs


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "gitauto/setup-20241224-120000-ABCD",
        },
    )


@patch("services.github.branches.delete_remote_branch.requests.delete")
def test_delete_branch_success(mock_delete: MagicMock):
    mock_delete.return_value.status_code = 204

    result = delete_remote_branch(base_args=_make_base_args())

    assert result is True
    mock_delete.assert_called_once()
    call_kwargs = mock_delete.call_args.kwargs
    assert "test-owner" in call_kwargs["url"]
    assert "test-repo" in call_kwargs["url"]
    assert "gitauto/setup-20241224-120000-ABCD" in call_kwargs["url"]


@patch("services.github.branches.delete_remote_branch.requests.delete")
def test_delete_branch_not_found(mock_delete: MagicMock):
    mock_delete.return_value.status_code = 404

    result = delete_remote_branch(base_args=_make_base_args())

    assert result is False


@patch("services.github.branches.delete_remote_branch.requests.delete")
def test_delete_branch_forbidden(mock_delete: MagicMock):
    mock_delete.return_value.status_code = 403

    result = delete_remote_branch(base_args=_make_base_args())

    assert result is False
