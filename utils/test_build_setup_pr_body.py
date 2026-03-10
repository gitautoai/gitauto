from utils.build_setup_pr_body import (
    SETUP_PR_TITLE,
    build_setup_pr_body,
)


def test_setup_pr_title():
    assert SETUP_PR_TITLE == "GitAuto setup"


def test_build_setup_pr_body_single_change():
    changes = ["Created tsconfig.test.json"]
    result = build_setup_pr_body(changes)

    assert "## Summary" in result
    assert "## Changes" in result
    assert "- Created tsconfig.test.json" in result


def test_build_setup_pr_body_multiple_changes():
    changes = ["Created tsconfig.test.json", "Updated .eslintrc.js"]
    result = build_setup_pr_body(changes)

    assert "- Created tsconfig.test.json" in result
    assert "- Updated .eslintrc.js" in result


def test_build_setup_pr_body_empty_changes():
    changes: list[str] = []
    result = build_setup_pr_body(changes)

    assert "## Summary" in result
    assert "## Changes" in result
