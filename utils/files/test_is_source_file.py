from utils.files.is_source_file import is_source_file


def test_source_files():
    assert is_source_file("src/index.ts") is True
    assert is_source_file("services/api_handler.py") is True
    assert is_source_file("app/components/Button.tsx") is True
    assert is_source_file("utils/helpers.py") is True
    assert is_source_file("lib/parser.js") is True


def test_test_files_excluded():
    assert is_source_file("test_user.py") is False
    assert is_source_file("src/Button.test.tsx") is False
    assert is_source_file("src/Button.spec.ts") is False
    assert is_source_file("__tests__/Button.tsx") is False
    assert is_source_file("tests/test_utils.py") is False


def test_config_files_excluded():
    assert is_source_file("jest.config.ts") is False
    assert is_source_file("vite.config.js") is False
    assert is_source_file(".eslintrc.js") is False
    assert is_source_file(".prettierrc.js") is False
    assert is_source_file("conftest.py") is False


def test_migration_files_excluded():
    assert is_source_file("migrations/001_init.py") is False
    assert is_source_file("migration_add_users.py") is False
    assert is_source_file("alembic/versions/abc123.py") is False


def test_type_files_excluded():
    assert is_source_file("services/github/types/user.py") is False
    assert is_source_file("user_types.py") is False
    assert is_source_file("constants/urls.py") is False
    assert is_source_file("schemas/user.py") is False
    assert is_source_file("index.d.ts") is False
    assert is_source_file("enums/status.py") is False


def test_dependency_files_excluded():
    assert is_source_file("vendor/phpoffice/phpspreadsheet/src/File.php") is False
    assert is_source_file("node_modules/lodash/index.js") is False
    assert is_source_file("php/lib/vendor/phpoffice/BaseParserClass.php") is False
    assert is_source_file("venv/lib/python3.13/site-packages/requests/api.py") is False
    assert is_source_file("Pods/AFNetworking/AFNetworking.m") is False


def test_non_code_files_excluded():
    assert is_source_file("README.md") is False
    assert is_source_file("package.json") is False
    assert is_source_file("styles.css") is False
    assert is_source_file("config.yaml") is False
    assert is_source_file("image.png") is False


def test_verb_prefix_type_files_are_source():
    # Files with verb prefixes that happen to contain "type" in the name
    assert is_source_file("services/stripe/get_billing_type.py") is True
    assert is_source_file("check_result_type.py") is True
    assert is_source_file("validate_schema.py") is True
