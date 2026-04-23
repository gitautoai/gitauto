import pytest

from utils.logs.label_log_source import label_log_source


def test_ours_header_says_our_infrastructure_in_all_caps():
    # The explicit "OUR" / "CUSTOMER" framing is the whole point of this function; a tag that just said "GitAuto Lambda" could still be misread as "Lambda must be the customer's Lambda". All-caps ownership prefix prevents that flip.
    result = label_log_source(
        "some lambda error",
        "ours",
        "GitAuto validation (AWS Lambda, Amazon Linux 2023)",
    )
    assert result.startswith("[log source: OUR infrastructure (GitAuto-controlled) — ")


def test_theirs_header_says_customer_infrastructure_in_all_caps():
    result = label_log_source(
        "some ci error", "theirs", "CircleCI for Foxquilt/foxden-version-controller"
    )
    assert result.startswith(
        "[log source: CUSTOMER infrastructure (their runtime/CI) — "
    )


def test_full_tagged_format_for_ours():
    assert label_log_source("E1", "ours", "X") == (
        "[log source: OUR infrastructure (GitAuto-controlled) — X]\nE1"
    )


def test_full_tagged_format_for_theirs():
    assert label_log_source("E2", "theirs", "Y") == (
        "[log source: CUSTOMER infrastructure (their runtime/CI) — Y]\nE2"
    )


def test_multiline_log_preserved():
    log = "line one\nline two\nline three"
    result = label_log_source(log, "theirs", "GitHub Actions for owner/repo")
    assert result == (
        "[log source: CUSTOMER infrastructure (their runtime/CI) — "
        "GitHub Actions for owner/repo]\n"
        "line one\nline two\nline three"
    )


def test_empty_log_returns_empty():
    # The webhook handler only attaches non-empty logs; no reason to tag an empty string.
    assert label_log_source("", "ours", "anything") == ""
    assert label_log_source("", "theirs", "anything") == ""


@pytest.mark.parametrize(
    "ownership, source, expected_prefix",
    [
        (
            "ours",
            "GitAuto validation (AWS Lambda, Amazon Linux 2023)",
            "[log source: OUR infrastructure (GitAuto-controlled) — GitAuto validation (AWS Lambda, Amazon Linux 2023)]\n",
        ),
        (
            "theirs",
            "CircleCI for Foxquilt/foxden-version-controller",
            "[log source: CUSTOMER infrastructure (their runtime/CI) — CircleCI for Foxquilt/foxden-version-controller]\n",
        ),
        (
            "theirs",
            "GitHub Actions for Foxquilt/foxden-version-controller",
            "[log source: CUSTOMER infrastructure (their runtime/CI) — GitHub Actions for Foxquilt/foxden-version-controller]\n",
        ),
        (
            "theirs",
            "Codecov coverage report for Foxquilt/foxden-version-controller",
            "[log source: CUSTOMER infrastructure (their runtime/CI) — Codecov coverage report for Foxquilt/foxden-version-controller]\n",
        ),
    ],
    ids=["lambda_ours", "circleci_theirs", "github_actions_theirs", "codecov_theirs"],
)
def test_known_sources_produce_expected_prefix(ownership, source, expected_prefix):
    result = label_log_source("whatever", ownership, source)
    assert result.startswith(expected_prefix)


def test_pr203_scenario_lambda_error_tagged_as_ours():
    # Real Lambda error from Foxquilt PR #203 (CloudWatch 2026-04-21 14:01:55).
    # Without the ownership prefix an agent could read the inner word "CircleCI"-free mention of libcrypto/MongoDB and still decide the fix belongs in the customer's repo. With "OUR infrastructure" at the front, the source is unambiguous on the first token.
    lambda_error = (
        "Starting the MongoMemoryServer Instance failed, enable debug log for more information. Error:\n"
        ' StdoutInstanceError: Instance failed to start because a library is missing or cannot be opened: "libcrypto.so.10"\n'
        "error Command failed with exit code 1."
    )
    labelled = label_log_source(
        lambda_error, "ours", "GitAuto validation (AWS Lambda, Amazon Linux 2023)"
    )
    first_line, rest = labelled.split("\n", 1)
    assert first_line == (
        "[log source: OUR infrastructure (GitAuto-controlled) — "
        "GitAuto validation (AWS Lambda, Amazon Linux 2023)]"
    )
    assert rest == lambda_error
