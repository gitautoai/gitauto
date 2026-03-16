# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

from scripts.sentry.resolve_issue import resolve_sentry_issue

MOCK_HEADERS = {
    "Authorization": "Bearer test-token",
    "Content-Type": "application/json",
}
MOCK_ORG = "test-org"


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_success(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-123", MOCK_HEADERS, MOCK_ORG)

    assert result is True
    mock_put.assert_called_once_with(
        "https://sentry.io/api/0/organizations/test-org/issues/AGENT-123/",
        headers=MOCK_HEADERS,
        json={"status": "resolved"},
        timeout=30,
    )


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_404(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-999", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_500(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-500", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_failure_401(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_put.return_value = mock_response

    result = resolve_sentry_issue("AGENT-401", MOCK_HEADERS, MOCK_ORG)

    assert result is False


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_url_construction(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("MY-ISSUE-42", MOCK_HEADERS, "custom-org")

    call_url = mock_put.call_args[0][0]
    assert call_url == "https://sentry.io/api/0/organizations/custom-org/issues/MY-ISSUE-42/"


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_sends_resolved_payload(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["json"] == {"status": "resolved"}


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_prints_done_on_success(mock_put, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    captured = capsys.readouterr()
    assert "Resolving AGENT-1..." in captured.out
    assert "done" in captured.out


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_prints_failed_on_error(mock_put, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    captured = capsys.readouterr()
    assert "Resolving AGENT-1..." in captured.out
    assert "failed (HTTP 403)" in captured.out


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_passes_headers(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    custom_headers = {"Authorization": "Bearer custom-token", "X-Custom": "value"}
    resolve_sentry_issue("AGENT-1", custom_headers, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["headers"] == custom_headers


@patch("scripts.sentry.resolve_issue.requests.put")
def test_resolve_sentry_issue_uses_30s_timeout(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    resolve_sentry_issue("AGENT-1", MOCK_HEADERS, MOCK_ORG)

    call_kwargs = mock_put.call_args[1]
    assert call_kwargs["timeout"] == 30


@patch("scripts.sentry.resolve_issue.sys.exit")
@patch("scripts.sentry.resolve_issue.os.getenv")
@patch("scripts.sentry.resolve_issue.argparse.ArgumentParser")
@patch("scripts.sentry.resolve_issue.resolve_sentry_issue")
def test_main_block_all_succeed(mock_resolve, mock_parser_cls, mock_getenv, mock_exit):
    mock_args = MagicMock()
    mock_args.issue_ids = ["AGENT-1", "AGENT-2"]
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_parser_cls.return_value = mock_parser

    mock_getenv.side_effect = lambda key: {
        "SENTRY_PERSONAL_TOKEN": "token",
        "SENTRY_ORG_SLUG": "org",
    }.get(key)

    mock_resolve.return_value = True

    import runpy

    with patch.dict("os.environ", {"SENTRY_PERSONAL_TOKEN": "token", "SENTRY_ORG_SLUG": "org"}):
        runpy.run_module("scripts.sentry.resolve_issue", run_name="__main__")

    assert mock_resolve.call_count == 2
    mock_exit.assert_not_called()


@patch("scripts.sentry.resolve_issue.sys.exit")
@patch("scripts.sentry.resolve_issue.os.getenv")
@patch("scripts.sentry.resolve_issue.argparse.ArgumentParser")
@patch("scripts.sentry.resolve_issue.resolve_sentry_issue")
def test_main_block_some_fail(mock_resolve, mock_parser_cls, mock_getenv, mock_exit):
    mock_args = MagicMock()
    mock_args.issue_ids = ["AGENT-1", "AGENT-2", "AGENT-3"]
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_parser_cls.return_value = mock_parser

    mock_getenv.side_effect = lambda key: {
        "SENTRY_PERSONAL_TOKEN": "token",
        "SENTRY_ORG_SLUG": "org",
    }.get(key)

    mock_resolve.side_effect = [True, False, True]

    import runpy

    with patch.dict("os.environ", {"SENTRY_PERSONAL_TOKEN": "token", "SENTRY_ORG_SLUG": "org"}):
        runpy.run_module("scripts.sentry.resolve_issue", run_name="__main__")

    mock_exit.assert_called_once_with(1)


@patch("scripts.sentry.resolve_issue.sys.exit")
@patch("scripts.sentry.resolve_issue.os.getenv")
@patch("scripts.sentry.resolve_issue.argparse.ArgumentParser")
def test_main_block_missing_env_vars(mock_parser_cls, mock_getenv, mock_exit):
    mock_args = MagicMock()
    mock_args.issue_ids = ["AGENT-1"]
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_parser_cls.return_value = mock_parser

    mock_getenv.return_value = None

    import runpy

    runpy.run_module("scripts.sentry.resolve_issue", run_name="__main__")

    mock_exit.assert_any_call(1)


@patch("scripts.sentry.resolve_issue.sys.exit")
@patch("scripts.sentry.resolve_issue.os.getenv")
@patch("scripts.sentry.resolve_issue.argparse.ArgumentParser")
def test_main_block_missing_token_only(mock_parser_cls, mock_getenv, mock_exit):
    mock_args = MagicMock()
    mock_args.issue_ids = ["AGENT-1"]
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_parser_cls.return_value = mock_parser

    mock_getenv.side_effect = lambda key: {
        "SENTRY_PERSONAL_TOKEN": None,
        "SENTRY_ORG_SLUG": "org",
    }.get(key)

    import runpy

    runpy.run_module("scripts.sentry.resolve_issue", run_name="__main__")

    mock_exit.assert_any_call(1)


@patch("scripts.sentry.resolve_issue.sys.exit")
@patch("scripts.sentry.resolve_issue.os.getenv")
@patch("scripts.sentry.resolve_issue.argparse.ArgumentParser")
def test_main_block_missing_org_only(mock_parser_cls, mock_getenv, mock_exit):
    mock_args = MagicMock()
    mock_args.issue_ids = ["AGENT-1"]
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_parser_cls.return_value = mock_parser

    mock_getenv.side_effect = lambda key: {
        "SENTRY_PERSONAL_TOKEN": "token",
        "SENTRY_ORG_SLUG": None,
    }.get(key)

    import runpy

    runpy.run_module("scripts.sentry.resolve_issue", run_name="__main__")

    mock_exit.assert_any_call(1)
