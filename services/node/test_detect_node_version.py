import os

import pytest

from constants.node import FALLBACK_NODE_VERSION
from services.node.detect_node_version import detect_node_version

REPOS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


@pytest.fixture
def repo_dir(tmp_path):
    return str(tmp_path)


def real_repo(path: str):
    """Skip if the repo directory doesn't exist (CI doesn't have local clones)."""
    if not os.path.isdir(path):
        pytest.skip(f"{os.path.basename(path)} repo not cloned")
    return path


# Real repos at ../website, ../Foxquilt/*, ../posthog, etc.
@pytest.mark.integration
class TestRealRepos:
    def test_website_engines_22x(self):
        repo = real_repo(os.path.join(REPOS_ROOT, "website"))
        assert detect_node_version(repo) == "22"

    def test_posthog_nvmrc_18(self):
        repo = real_repo(os.path.join(REPOS_ROOT, "posthog"))
        assert detect_node_version(repo) == "18"

    def test_ghostwriter_engines_gte_22(self):
        repo = real_repo(os.path.join(REPOS_ROOT, "ghostwriter"))
        assert detect_node_version(repo) == "22"

    def test_slackgpt3_engines_22(self):
        repo = real_repo(os.path.join(REPOS_ROOT, "slackgpt3"))
        assert detect_node_version(repo) == "22"

    def test_foxcom_forms_no_version_defaults_to_22(self):
        repo = real_repo(os.path.join(REPOS_ROOT, "Foxquilt", "foxcom-forms"))
        assert detect_node_version(repo) == FALLBACK_NODE_VERSION

    def test_foxden_admin_portal_backend_no_version_defaults_to_22(self):
        repo = real_repo(
            os.path.join(REPOS_ROOT, "Foxquilt", "foxden-admin-portal-backend")
        )
        assert detect_node_version(repo) == FALLBACK_NODE_VERSION


# Solitary tests with tmp_path fixtures
class TestNvmrc:
    def test_major_only(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".nvmrc"), "w", encoding="utf-8") as f:
            f.write("18\n")
        assert detect_node_version(repo_dir) == "18"

    def test_full_version(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".nvmrc"), "w", encoding="utf-8") as f:
            f.write("v20.11.0\n")
        assert detect_node_version(repo_dir) == "20"

    def test_v_prefix(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".nvmrc"), "w", encoding="utf-8") as f:
            f.write("v22\n")
        assert detect_node_version(repo_dir) == "22"

    def test_lts_falls_through_to_default(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".nvmrc"), "w", encoding="utf-8") as f:
            f.write("lts/*\n")
        assert detect_node_version(repo_dir) == FALLBACK_NODE_VERSION


class TestNodeVersionFile:
    def test_node_version_file(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".node-version"), "w", encoding="utf-8") as f:
            f.write("20.10.0\n")
        assert detect_node_version(repo_dir) == "20"

    def test_nvmrc_takes_precedence(self, repo_dir: str):
        with open(os.path.join(repo_dir, ".nvmrc"), "w", encoding="utf-8") as f:
            f.write("22\n")
        with open(os.path.join(repo_dir, ".node-version"), "w", encoding="utf-8") as f:
            f.write("20\n")
        assert detect_node_version(repo_dir) == "22"


class TestDefault:
    def test_empty_dir_returns_default(self, repo_dir: str):
        assert detect_node_version(repo_dir) == FALLBACK_NODE_VERSION
