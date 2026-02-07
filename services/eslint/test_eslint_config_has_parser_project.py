import json

from services.eslint.eslint_config_has_parser_project import (
    eslint_config_has_parser_project,
)


def test_json_config_with_parser_project():
    config = {
        "filename": ".eslintrc.json",
        "content": json.dumps({"parserOptions": {"project": "./tsconfig.eslint.json"}}),
    }
    assert eslint_config_has_parser_project(config) is True


def test_json_config_with_parser_project_in_overrides():
    config = {
        "filename": ".eslintrc.json",
        "content": json.dumps(
            {
                "overrides": [
                    {
                        "files": ["*.ts"],
                        "parserOptions": {"project": "./tsconfig.json"},
                    }
                ]
            }
        ),
    }
    assert eslint_config_has_parser_project(config) is True


def test_json_config_without_project():
    config = {
        "filename": ".eslintrc.json",
        "content": json.dumps({"parserOptions": {"ecmaVersion": 2020}}),
    }
    assert eslint_config_has_parser_project(config) is False


def test_empty_json_config():
    config = {"filename": ".eslintrc.json", "content": "{}"}
    assert eslint_config_has_parser_project(config) is False


def test_js_config_with_project():
    config = {
        "filename": ".eslintrc.js",
        "content": "module.exports = { parserOptions: { project: './tsconfig.json' } }",
    }
    assert eslint_config_has_parser_project(config) is True


def test_js_config_without_project():
    config = {
        "filename": "eslint.config.js",
        "content": "export default { rules: {} }",
    }
    assert eslint_config_has_parser_project(config) is False


def test_eslintrc_no_extension():
    """Test .eslintrc (no extension) which is JSON format."""
    config = {
        "filename": ".eslintrc",
        "content": json.dumps({"parserOptions": {"project": "./tsconfig.eslint.json"}}),
    }
    assert eslint_config_has_parser_project(config) is True


def test_empty_content():
    config = {"filename": ".eslintrc.json", "content": ""}
    assert eslint_config_has_parser_project(config) is False
