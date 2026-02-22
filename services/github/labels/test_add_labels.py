from unittest.mock import MagicMock, patch

from services.github.labels.add_labels import add_labels


@patch("services.github.labels.add_labels.requests.post")
@patch("services.github.labels.add_labels.create_headers")
def test_add_labels_success(mock_create_headers, mock_post):
    mock_create_headers.return_value = {"Authorization": "token abc"}
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    add_labels(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        token="test-token",
        labels=["gitauto", "bug"],
    )

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"] == {"labels": ["gitauto", "bug"]}
    assert "repos/test-owner/test-repo/issues/42/labels" in call_kwargs["url"]


@patch("services.github.labels.add_labels.requests.post")
@patch("services.github.labels.add_labels.create_headers")
def test_add_labels_empty_list(mock_create_headers, mock_post):
    mock_create_headers.return_value = {"Authorization": "token abc"}
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    add_labels(
        owner="test-owner",
        repo="test-repo",
        pr_number=1,
        token="test-token",
        labels=[],
    )

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"] == {"labels": []}
