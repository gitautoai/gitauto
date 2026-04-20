# pylint: disable=use-implicit-booleaness-not-comparison
# CLAUDE.md requires exact `== expected` assertions. `== {}` is more explicit than `not result` and pylint's preference conflicts with that rule here.
from services.http.github_auth_headers import github_auth_headers


def test_no_token_returns_empty_dict():
    assert github_auth_headers("https://api.github.com/repos/foo/bar", None) == {}


def test_empty_token_returns_empty_dict():
    assert github_auth_headers("https://api.github.com/repos/foo/bar", "") == {}


def test_api_github_with_token_adds_bearer():
    assert github_auth_headers(
        "https://api.github.com/repos/foo/bar/contents/x?ref=abc", "ghs_test"
    ) == {"Authorization": "Bearer ghs_test"}


def test_raw_githubusercontent_with_token_adds_bearer():
    assert github_auth_headers(
        "https://raw.githubusercontent.com/foo/bar/abc/file.ts", "ghs_test"
    ) == {"Authorization": "Bearer ghs_test"}


def test_unrelated_host_returns_empty_even_with_token():
    assert github_auth_headers("https://example.com/some/path", "ghs_test") == {}


def test_github_com_ui_host_not_covered():
    """github.com (the UI) isn't in the list — it doesn't serve file content
    directly, so we shouldn't leak a Bearer token to random HTML endpoints."""
    assert github_auth_headers("https://github.com/foo/bar", "ghs_test") == {}


def test_invalid_url_returns_empty():
    assert github_auth_headers("not a url", "ghs_test") == {}
