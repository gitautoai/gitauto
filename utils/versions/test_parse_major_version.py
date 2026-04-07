from utils.versions.parse_major_version import parse_major_version


# Real .nvmrc / .node-version values from cloned repos
class TestRealVersionStrings:
    def test_posthog_nvmrc_18(self):
        # ../posthog/.nvmrc = "18"
        assert parse_major_version("18") == "18"


class TestSyntheticVersionStrings:
    def test_v_prefix_full(self):
        assert parse_major_version("v22.1.0") == "22"

    def test_v_prefix_major_only(self):
        assert parse_major_version("v20") == "20"

    def test_lts_returns_none(self):
        assert parse_major_version("lts/hydrogen") is None

    def test_empty_string(self):
        assert parse_major_version("") is None
