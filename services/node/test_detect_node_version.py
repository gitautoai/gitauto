import os

import pytest

from services.node.detect_node_version import DEFAULT_NODE_VERSION, detect_node_version

REPOS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


@pytest.fixture
def repo_dir(tmp_path):
    return str(tmp_path)


# Real repos at ../website, ../Foxquilt/*, ../posthog, etc.
# Skipped in CI where these repos don't exist
@pytest.mark.integration
class TestRealRepos:
    def test_website_engines_22x(self):
        # ../website/package.json has engines.node = "22.x"
        repo = os.path.join(REPOS_ROOT, "website")
        if not os.path.isdir(repo):
            pytest.skip("website repo not cloned")
        assert detect_node_version(repo) == "22"

    def test_posthog_nvmrc_18(self):
        # ../posthog/.nvmrc = "18", engines.node = ">=18 <19"
        # .nvmrc takes precedence
        repo = os.path.join(REPOS_ROOT, "posthog")
        if not os.path.isdir(repo):
            pytest.skip("posthog repo not cloned")
        assert detect_node_version(repo) == "18"

    def test_ghostwriter_engines_gte_22(self):
        # ../ghostwriter/package.json has engines.node = ">=22.0.0"
        repo = os.path.join(REPOS_ROOT, "ghostwriter")
        if not os.path.isdir(repo):
            pytest.skip("ghostwriter repo not cloned")
        assert detect_node_version(repo) == "22"

    def test_slackgpt3_engines_22(self):
        # ../slackgpt3/package.json has engines.node = "22"
        repo = os.path.join(REPOS_ROOT, "slackgpt3")
        if not os.path.isdir(repo):
            pytest.skip("slackgpt3 repo not cloned")
        assert detect_node_version(repo) == "22"

    def test_foxcom_forms_no_version_defaults_to_22(self):
        # Fox repos have no .nvmrc, no .node-version, no engines.node
        repo = os.path.join(REPOS_ROOT, "Foxquilt", "foxcom-forms")
        if not os.path.isdir(repo):
            pytest.skip("foxcom-forms repo not cloned")
        assert detect_node_version(repo) == DEFAULT_NODE_VERSION

    def test_foxden_admin_portal_backend_no_version_defaults_to_22(self):
        # This is the repo that failed with Node 24 - should default to 22
        repo = os.path.join(REPOS_ROOT, "Foxquilt", "foxden-admin-portal-backend")
        if not os.path.isdir(repo):
            pytest.skip("foxden-admin-portal-backend repo not cloned")
        assert detect_node_version(repo) == DEFAULT_NODE_VERSION


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
        assert detect_node_version(repo_dir) == DEFAULT_NODE_VERSION


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
        assert detect_node_version(repo_dir) == DEFAULT_NODE_VERSION
