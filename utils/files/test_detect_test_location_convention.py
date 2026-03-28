import os
import tempfile

from utils.files.detect_test_location_convention import detect_test_location_convention


def _create_files(base: str, paths: list[str]):
    for p in paths:
        full = os.path.join(base, p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write("")


def test_co_located_convention():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/utils/foo.ts",
                "src/utils/foo.test.ts",
                "src/models/bar.ts",
                "src/models/bar.test.ts",
                "src/index.ts",
                "src/index.test.ts",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("co-located")


def test_tests_subdirectory_convention():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/utils/foo.ts",
                "src/utils/__tests__/foo.test.ts",
                "src/models/bar.ts",
                "src/models/__tests__/bar.test.ts",
                "src/services/__tests__/baz.test.ts",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("__tests__")


def test_separate_test_directory_convention():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/utils/foo.py",
                "src/models/bar.py",
                "tests/utils/test_foo.py",
                "tests/models/test_bar.py",
                "tests/test_baz.py",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("separate")


def test_mixed_below_threshold_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/utils/foo.test.ts",
                "src/utils/__tests__/bar.test.ts",
                "tests/test_baz.py",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is None


def test_empty_repo_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(tmp, ["src/utils/foo.ts", "src/models/bar.ts"])
        result = detect_test_location_convention(tmp)
        assert result is None


def test_skips_node_modules():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "node_modules/pkg/__tests__/foo.test.js",
                "node_modules/pkg/__tests__/bar.test.js",
                "node_modules/pkg/__tests__/baz.test.js",
                "src/utils/foo.test.ts",
                "src/models/bar.test.ts",
                "src/services/baz.test.ts",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("co-located")


def test_separate_with_test_prefix_naming():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/foo.py",
                "test/test_foo.py",
                "test/test_bar.py",
                "test/test_baz.py",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("separate")


def test_spec_directory_counts_as_separate():
    with tempfile.TemporaryDirectory() as tmp:
        _create_files(
            tmp,
            [
                "src/foo.rb",
                "spec/foo_spec.rb",
                "spec/bar_spec.rb",
                "spec/baz_spec.rb",
            ],
        )
        result = detect_test_location_convention(tmp)
        assert result is not None
        assert result.startswith("separate")
