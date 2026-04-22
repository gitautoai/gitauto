# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

import pytest

from services.mongoms.get_archive_name import get_mongoms_archive_name


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_with_explicit_version(_mock_major, _mock_version):
    """mongoms 7.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=9)
def test_mongoms_9x_with_explicit_7x_version(_mock_major, _mock_version):
    """mongoms 9.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=10
)
def test_mongoms_10x_with_explicit_7x_version(_mock_major, _mock_version):
    """mongoms 10.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=9)
def test_mongoms_9x_no_explicit_version_uses_rhel90_distro(_mock_major, _mock_version):
    """mongoms 9.x with no explicit version stays on upstream's MongoDB 6.0.9 default — GA must test the same version the customer's CI does.
    The broken archive was `amazon2-6.0.9` (libcrypto.so.10, not on AL2023). `rhel90-6.0.9` shares AL2023's glibc + OpenSSL 3 ABI and actually runs on Lambda.
    """
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-rhel90-6.0.9.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=10
)
def test_mongoms_10x_no_explicit_version_uses_default(_mock_major, _mock_version):
    """mongoms 10.x with no explicit version falls back to default 7.0.11 with amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-7.0.11.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_no_explicit_version_uses_rhel90_distro(_mock_major, _mock_version):
    """mongoms 7.x with no explicit version: same rationale as the 9.x case — upstream default 6.0.9 with rhel90 distro so the binary actually runs on AL2023."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-rhel90-6.0.9.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=12
)
def test_mongoms_future_version_falls_back_to_latest_known(_mock_major, _mock_version):
    """mongoms 12.x (unmapped) falls back to highest known default (11 -> 8.2.1)."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-8.2.1.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=5)
def test_mongoms_old_version_returns_none(_mock_major, _mock_version):
    """mongoms 5.x (too old, not mapped) returns None."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=None
)
def test_no_mongoms_in_package_json(_mock_major):
    """mongodb-memory-server not in package.json."""
    assert get_mongoms_archive_name("/tmp/clone") is None


# Snapshot of every Foxquilt repo at /Users/rwest/Repositories/Foxquilt on 2026-04-21.
# Columns: mongoms major (from direct dep or transitive via @shelf/jest-mongodb in yarn.lock), explicit MongoDB version detected by get_mongodb_server_version (package.json script MONGOMS_VERSION= OR jest-mongodb-config.js binary.version), and the archive name get_mongoms_archive_name must produce post-fix.
# `None` for mongoms_major means the repo doesn't use Mongo at all; the expected archive is `None` (no pre-cache needed).
# Every Mongo-using repo must resolve to a distro in AL2023_COMPATIBLE_DISTROS. `amazon2` would crash our Lambda with libcrypto.so.10 missing.
FOXQUILT_REPO_CASES = [
    ("foxcom-forms", None, None, None),
    (
        "foxcom-forms-backend",
        7,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    (
        "foxcom-payment-backend",
        7,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    ("foxcom-payment-frontend", None, None, None),
    ("foxden-admin-portal", None, None, None),
    (
        "foxden-admin-portal-backend",
        9,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    (
        "foxden-auth-service",
        9,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    ("foxden-billing", 10, None, "mongodb-linux-x86_64-amazon2023-7.0.11.tgz"),
    (
        "foxden-policy-document-backend",
        9,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    (
        "foxden-rating-quoting-backend",
        9,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    # Default path — upstream mongoms 9.x default is 6.0.9 (no amazon2023 build); must fall back to rhel90 which shares AL2023's glibc/OpenSSL ABI.
    ("foxden-shared-lib", 9, None, "mongodb-linux-x86_64-rhel90-6.0.9.tgz"),
    (
        "foxden-tools",
        9,
        "v7.0-latest",
        "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz",
    ),
    (
        "foxden-version-controller",
        9,
        "v8.0-latest",
        "mongodb-linux-x86_64-amazon2023-v8.0-latest.tgz",
    ),
    ("foxden-version-controller-client", None, None, None),
]

# SONAMEs present on our AL2023 Lambda. Any distro whose binary dynamically links against these runs on Lambda. `amazon2` does not — it wants libcrypto.so.10 (OpenSSL 1.0.x) which AL2023 removed.
AL2023_COMPATIBLE_DISTROS = ("amazon2023", "rhel90")


def test_foxquilt_repo_cases_cover_all_14_repos():
    # If Foxquilt adds/removes a repo, update FOXQUILT_REPO_CASES and this number.
    assert len(FOXQUILT_REPO_CASES) == 14


@pytest.mark.parametrize(
    "repo_name, mongoms_major, explicit_version, expected_archive",
    FOXQUILT_REPO_CASES,
    ids=[case[0] for case in FOXQUILT_REPO_CASES],
)
def test_every_foxquilt_repo_resolves_to_al2023_archive(
    repo_name, mongoms_major, explicit_version, expected_archive
):
    with patch(
        "services.mongoms.get_archive_name.get_dependency_major_version",
        return_value=mongoms_major,
    ), patch(
        "services.mongoms.get_archive_name.get_mongodb_server_version",
        return_value=explicit_version,
    ):
        actual = get_mongoms_archive_name(f"/tmp/{repo_name}")
    assert (
        actual == expected_archive
    ), f"{repo_name} produced {actual!r}; expected {expected_archive!r}"
    if expected_archive is None:
        # Non-Mongo repo — nothing to pre-cache, nothing to check for ABI compat.
        return
    assert actual is not None and any(
        d in actual for d in AL2023_COMPATIBLE_DISTROS
    ), f"{repo_name} produced {actual!r}; expected a distro from {AL2023_COMPATIBLE_DISTROS} so the binary can actually run on AL2023 Lambda"
