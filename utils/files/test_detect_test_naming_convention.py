# pylint: disable=missing-module-docstring
import os

from utils.files.detect_test_naming_convention import detect_test_naming_convention


def _create_files(base_dir: str, filenames: list[str]):
    for name in filenames:
        filepath = os.path.join(base_dir, name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")


# JS/TS: .spec. vs .test.


def test_js_spec_convention(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/models/User.spec.ts",
            "src/models/Order.spec.ts",
            "src/utils/helper.spec.js",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert ".spec." in result


def test_js_test_convention(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/models/User.test.ts",
            "src/models/Order.test.tsx",
            "src/utils/helper.test.js",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert ".test." in result


# Python: test_ prefix


def test_python_test_prefix(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "tests/test_user.py",
            "tests/test_order.py",
            "tests/test_billing.py",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "test_ prefix" in result


# PHP/Java: XxxTest suffix


def test_php_test_suffix(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "tests/UserTest.php",
            "tests/OrderTest.php",
            "tests/BillingTest.php",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "Test suffix" in result


def test_java_test_suffix(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/test/java/com/example/UserTest.java",
            "src/test/java/com/example/OrderTest.java",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "Test suffix" in result


# Go: _test.go


def test_go_underscore_test(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "pkg/user_test.go",
            "pkg/order_test.go",
            "internal/billing_test.go",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "_test suffix" in result


# Ruby: _spec.rb (RSpec)


def test_ruby_underscore_spec(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "spec/models/user_spec.rb",
            "spec/models/order_spec.rb",
            "spec/services/billing_spec.rb",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "_spec suffix" in result


# Mixed within same ecosystem


def test_mixed_js_spec_dominant(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/User.spec.ts",
            "src/Order.spec.ts",
            "src/Product.spec.ts",
            "src/helper.test.js",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert ".spec." in result


def test_mixed_no_clear_winner(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/User.spec.ts",
            "src/Order.test.ts",
        ],
    )
    assert detect_test_naming_convention(str(tmp_path)) is None


# Edge cases


def test_empty_repo(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "src/models/User.ts",
            "src/utils/helper.js",
        ],
    )
    assert detect_test_naming_convention(str(tmp_path)) is None


def test_no_files_at_all(tmp_path: str):
    assert detect_test_naming_convention(str(tmp_path)) is None


def test_skips_node_modules(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "node_modules/lib/foo.test.js",
            "node_modules/lib/bar.test.js",
            "src/models/User.spec.ts",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert ".spec." in result


def test_includes_example_filename(tmp_path: str):
    _create_files(
        str(tmp_path),
        [
            "tests/UserTest.php",
            "tests/OrderTest.php",
        ],
    )
    result = detect_test_naming_convention(str(tmp_path))
    assert result is not None
    assert "UserTest.php" in result or "OrderTest.php" in result
