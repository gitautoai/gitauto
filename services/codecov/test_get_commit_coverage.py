from unittest.mock import Mock, patch


from services.codecov.get_commit_coverage import get_codecov_commit_coverage


@patch("services.codecov.get_commit_coverage.requests.get")
def test_get_codecov_commit_coverage_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totals": {
            "files": 2,
            "lines": 100,
            "hits": 80,
            "misses": 15,
            "partials": 5,
            "coverage": 80.0,
            "branches": 10,
            "methods": 5,
            "messages": 0,
            "sessions": 1,
            "complexity": 10,
            "complexity_total": 20,
            "complexity_ratio": 0.5,
            "diff": {},
        },
        "files": [
            {
                "name": "src/app.py",
                "totals": {
                    "files": 1,
                    "lines": 50,
                    "hits": 40,
                    "misses": 8,
                    "partials": 2,
                    "coverage": 80.0,
                    "branches": 5,
                    "methods": 3,
                    "messages": 0,
                    "sessions": 1,
                    "complexity": 5,
                    "complexity_total": 10,
                    "complexity_ratio": 0.5,
                    "diff": {},
                },
                "line_coverage": [0, 1, 1, 0, 2, 0, 1],
            },
            {
                "name": "src/utils.py",
                "totals": {
                    "files": 1,
                    "lines": 50,
                    "hits": 40,
                    "misses": 7,
                    "partials": 3,
                    "coverage": 80.0,
                    "branches": 5,
                    "methods": 2,
                    "messages": 0,
                    "sessions": 1,
                    "complexity": 5,
                    "complexity_total": 10,
                    "complexity_ratio": 0.5,
                    "diff": {},
                },
                "line_coverage": [0, 0, 1, 2, 2],
            },
        ],
        "commit_file_url": "https://app.codecov.io/gh/owner/repo/commit/abc123",
    }
    mock_get.return_value = mock_response

    result = get_codecov_commit_coverage(
        owner="owner",
        repo="repo",
        commit_sha="abc123",
        codecov_token="test_token",
        service="github",
    )

    assert result is not None
    assert len(result) == 2

    assert result[0]["name"] == "src/app.py"
    assert result[0]["coverage"] == 80.0
    assert result[0]["uncovered_lines"] == [2, 3, 7]
    assert result[0]["partially_covered_lines"] == [5]

    assert result[1]["name"] == "src/utils.py"
    assert result[1]["coverage"] == 80.0
    assert result[1]["uncovered_lines"] == [3]
    assert result[1]["partially_covered_lines"] == [4, 5]

    mock_get.assert_called_once_with(
        "https://api.codecov.io/api/v2/github/owner/repos/repo/commits/abc123/",
        headers={"Authorization": "Bearer test_token", "Accept": "application/json"},
        timeout=120,
    )


@patch("services.codecov.get_commit_coverage.requests.get")
def test_get_codecov_commit_coverage_with_gitlab_service(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totals": {},
        "files": [],
        "commit_file_url": "https://app.codecov.io/gl/owner/repo/commit/abc123",
    }
    mock_get.return_value = mock_response

    result = get_codecov_commit_coverage(
        owner="owner",
        repo="repo",
        commit_sha="abc123",
        codecov_token="test_token",
        service="gitlab",
    )

    assert not result
    mock_get.assert_called_once_with(
        "https://api.codecov.io/api/v2/gitlab/owner/repos/repo/commits/abc123/",
        headers={"Authorization": "Bearer test_token", "Accept": "application/json"},
        timeout=120,
    )


@patch("services.codecov.get_commit_coverage.requests.get")
def test_get_codecov_commit_coverage_http_error(mock_get):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception("Not found")
    mock_get.return_value = mock_response

    result = get_codecov_commit_coverage(
        owner="owner",
        repo="repo",
        commit_sha="abc123",
        codecov_token="test_token",
    )

    assert result is None


@patch("services.codecov.get_commit_coverage.requests.get")
def test_get_codecov_commit_coverage_empty_files(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totals": {},
        "files": [],
        "commit_file_url": "https://app.codecov.io/gh/owner/repo/commit/abc123",
    }
    mock_get.return_value = mock_response

    result = get_codecov_commit_coverage(
        owner="owner",
        repo="repo",
        commit_sha="abc123",
        codecov_token="test_token",
    )

    assert not result
