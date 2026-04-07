from utils.versions.extract_max_major_from_constraint import (
    extract_max_major_from_constraint,
)


# Real engines.node values from cloned repos
class TestRealNodeConstraints:
    def test_website_22x(self):
        # ../website/package.json engines.node
        assert extract_max_major_from_constraint("22.x") == "22"

    def test_posthog_gte18_lt19(self):
        # ../posthog/package.json engines.node
        assert extract_max_major_from_constraint(">=18 <19") == "18"

    def test_ghostwriter_gte22(self):
        # ../ghostwriter/package.json engines.node
        assert extract_max_major_from_constraint(">=22.0.0") == "22"

    def test_slackgpt3_22(self):
        # ../slackgpt3/package.json engines.node
        assert extract_max_major_from_constraint("22") == "22"


# Real require.php values from cloned repos
class TestRealPhpConstraints:
    def test_spiderplus_web_gte56(self):
        # ../SPIDERPLUS/SPIDERPLUS-web/composer.json require.php
        assert extract_max_major_from_constraint(">=5.6") == "5"


class TestSyntheticConstraints:
    def test_caret(self):
        assert extract_max_major_from_constraint("^18") == "18"

    def test_multiple_or(self):
        assert extract_max_major_from_constraint("^18 || ^20 || ^22") == "22"

    def test_tilde(self):
        assert extract_max_major_from_constraint("~20.10.0") == "20"

    def test_python3(self):
        # Python major version 3 — must not be filtered out
        assert extract_max_major_from_constraint(">=3.12") == "3"

    def test_no_numbers(self):
        assert extract_max_major_from_constraint("latest") is None
