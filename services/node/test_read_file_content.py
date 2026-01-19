from unittest.mock import mock_open, patch

from services.node.read_file_content import read_file_content


def test_read_from_clone_dir():
    with patch("services.node.read_file_content.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data='{"name": "test"}')):
            result = read_file_content(
                "package.json",
                clone_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )
            assert result == '{"name": "test"}'


def test_fallback_to_github_api():
    with patch("services.node.read_file_content.os.path.exists") as mock_exists:
        with patch("services.node.read_file_content.get_raw_content") as mock_get:
            with patch("services.node.read_file_content.os.makedirs") as mock_makedirs:
                with patch("builtins.open", mock_open()):
                    mock_exists.return_value = False
                    mock_get.return_value = '{"name": "test"}'

                    result = read_file_content(
                        "package.json",
                        clone_dir="/tmp/repo",
                        owner="owner",
                        repo="repo",
                        branch="main",
                        token="token",
                    )

                    assert result == '{"name": "test"}'
                    mock_get.assert_called_once_with(
                        owner="owner",
                        repo="repo",
                        file_path="package.json",
                        ref="main",
                        token="token",
                    )
                    mock_makedirs.assert_called_once_with("/tmp/repo", exist_ok=True)


def test_github_api_when_no_clone_dir():
    with patch("services.node.read_file_content.get_raw_content") as mock_get:
        mock_get.return_value = '{"name": "test"}'

        result = read_file_content(
            "package.json",
            clone_dir=None,
            owner="owner",
            repo="repo",
            branch="main",
            token="token",
        )

        assert result == '{"name": "test"}'


def test_returns_none_when_file_not_found():
    with patch("services.node.read_file_content.os.path.exists") as mock_exists:
        with patch("services.node.read_file_content.get_raw_content") as mock_get:
            mock_exists.return_value = False
            mock_get.return_value = None

            result = read_file_content(
                ".npmrc",
                clone_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert result is None


def test_creates_nested_parent_dirs_when_caching():
    with patch("services.node.read_file_content.os.path.exists") as mock_exists:
        with patch("services.node.read_file_content.get_raw_content") as mock_get:
            with patch("services.node.read_file_content.os.makedirs") as mock_makedirs:
                with patch("builtins.open", mock_open()):
                    mock_exists.return_value = False
                    mock_get.return_value = '{"name": "test"}'

                    result = read_file_content(
                        "subdir/nested/package.json",
                        clone_dir="/tmp/repo",
                        owner="owner",
                        repo="repo",
                        branch="main",
                        token="token",
                    )

                    assert result == '{"name": "test"}'
                    mock_makedirs.assert_called_once_with(
                        "/tmp/repo/subdir/nested", exist_ok=True
                    )
