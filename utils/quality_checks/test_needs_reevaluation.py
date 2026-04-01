# pyright: reportUnusedVariable=false
from datetime import datetime, timezone
from typing import cast

from schemas.supabase.types import Coverages
from utils.quality_checks.needs_reevaluation import needs_quality_reevaluation


def _make_coverage(
    quality_checks=None,
    impl_blob_sha=None,
    test_blob_sha=None,
    checklist_hash=None,
) -> Coverages:
    return cast(
        Coverages,
        {
            "id": 1,
            "full_path": "src/utils/foo.ts",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "user",
            "updated_by": "user",
            "level": "file",
            "file_size": 100,
            "statement_coverage": 100.0,
            "function_coverage": 100.0,
            "branch_coverage": 100.0,
            "line_coverage": 100.0,
            "package_name": None,
            "language": None,
            "github_issue_url": None,
            "is_excluded_from_testing": False,
            "exclusion_reason": None,
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "impl_blob_sha": impl_blob_sha,
            "test_blob_sha": test_blob_sha,
            "checklist_hash": checklist_hash,
            "quality_checks": quality_checks,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    )


def test_needs_reeval_when_quality_checks_null():
    coverage = _make_coverage(quality_checks=None)
    assert needs_quality_reevaluation(coverage, "sha1", "sha2", "hash1") is True


def test_no_reeval_when_nothing_changed():
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha="sha2",
        checklist_hash="hash1",
    )
    assert needs_quality_reevaluation(coverage, "sha1", "sha2", "hash1") is False


def test_needs_reeval_when_impl_changed():
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="old_sha",
        test_blob_sha="sha2",
        checklist_hash="hash1",
    )
    assert needs_quality_reevaluation(coverage, "new_sha", "sha2", "hash1") is True


def test_needs_reeval_when_test_changed():
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha="old_test_sha",
        checklist_hash="hash1",
    )
    assert needs_quality_reevaluation(coverage, "sha1", "new_test_sha", "hash1") is True


def test_needs_reeval_when_checklist_changed():
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha="sha2",
        checklist_hash="old_hash",
    )
    assert needs_quality_reevaluation(coverage, "sha1", "sha2", "new_hash") is True


def test_needs_reeval_when_test_sha_none_both_sides():
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha=None,
        checklist_hash="hash1",
    )
    # Both None = no change
    assert needs_quality_reevaluation(coverage, "sha1", None, "hash1") is False


def test_needs_reeval_when_stored_test_sha_exists_but_current_is_none():
    # Test file was deleted since last check
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha="old_test_sha",
        checklist_hash="hash1",
    )
    assert needs_quality_reevaluation(coverage, "sha1", None, "hash1") is True


def test_needs_reeval_when_stored_test_sha_none_but_current_exists():
    # Test file was created since last check
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha=None,
        checklist_hash="hash1",
    )
    assert needs_quality_reevaluation(coverage, "sha1", "new_test_sha", "hash1") is True


def test_needs_reeval_when_stored_checklist_hash_none():
    # First run after adding checklist_hash column
    coverage = _make_coverage(
        quality_checks={"adversarial": {}},
        impl_blob_sha="sha1",
        test_blob_sha="sha2",
        checklist_hash=None,
    )
    assert needs_quality_reevaluation(coverage, "sha1", "sha2", "hash1") is True
