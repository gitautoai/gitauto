# pylint: disable=unused-argument
import json
from unittest.mock import patch

import pytest
from services.github.files.get_eslint_config import get_eslint_config

REAL_CUSTOMER_ESLINTRC = """{
  "parser": "@typescript-eslint/parser",
  "env": {
    "node": true
  },
  "parserOptions": {
    "ecmaVersion": 2020,
    "project": "./tsconfig.json",
    "sourceType": "module"
  },
  "extends": [
    "eslint:recommended",
    "plugin:import/errors",
    "plugin:import/warnings",
    "plugin:import/typescript",
    "plugin:@typescript-eslint/recommended",
    "plugin:prettier/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-var-requires": "off",
    "no-console": "warn",
    "simple-import-sort/exports": "error",
    "simple-import-sort/imports": "error"
  },
  "plugins": ["import", "simple-import-sort"],
  "ignorePatterns": [
    "jest.config.js",
    "migrate-mongo*",
    ".eslintrc.js",
    "serviceWorker.ts",
    "generated",
    "*.css",
    "*.svg",
    "*.jpg",
    "*.png",
    "webpack.config.js",
    "**/*.test.ts",
    "**/*.test.js",
    "**/*.spec.ts",
    "**/test/**",
    "**/__tests__/**"
  ]
}"""


@pytest.fixture
def base_args():
    return {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "base_branch": "main",
    }


def test_get_eslint_config_finds_eslintrc_json(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.json":
                return REAL_CUSTOMER_ESLINTRC
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.json"
        assert result["content"] == REAL_CUSTOMER_ESLINTRC


def test_get_eslint_config_finds_eslintrc_js(base_args):
    eslintrc_js = """module.exports = {
  parser: '@typescript-eslint/parser',
  rules: {
    'no-console': 'warn'
  }
};"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.js":
                return eslintrc_js
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.js"
        assert result["content"] == eslintrc_js


def test_get_eslint_config_finds_eslintrc_yml(base_args):
    eslintrc_yml = """parser: '@typescript-eslint/parser'
rules:
  no-console: warn"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.yml":
                return eslintrc_yml
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.yml"
        assert result["content"] == eslintrc_yml


def test_get_eslint_config_finds_eslintrc_yaml(base_args):
    eslintrc_yaml = """parser: '@typescript-eslint/parser'
rules:
  no-console: error"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.yaml":
                return eslintrc_yaml
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.yaml"
        assert result["content"] == eslintrc_yaml


def test_get_eslint_config_finds_eslintrc(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc":
                return REAL_CUSTOMER_ESLINTRC
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc"
        assert result["content"] == REAL_CUSTOMER_ESLINTRC

        config = json.loads(result["content"])
        assert config["parser"] == "@typescript-eslint/parser"
        assert "simple-import-sort/imports" in config["rules"]


def test_get_eslint_config_finds_eslint_config_js(base_args):
    eslint_config_js = """export default {
  parser: '@typescript-eslint/parser',
  rules: {
    'no-console': 'warn'
  }
};"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "eslint.config.js":
                return eslint_config_js
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "eslint.config.js"
        assert result["content"] == eslint_config_js


def test_get_eslint_config_finds_eslint_config_mjs(base_args):
    eslint_config_mjs = """export default {
  parser: '@typescript-eslint/parser',
  rules: {
    'no-console': 'error'
  }
};"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "eslint.config.mjs":
                return eslint_config_mjs
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "eslint.config.mjs"
        assert result["content"] == eslint_config_mjs


def test_get_eslint_config_finds_eslint_config_cjs(base_args):
    eslint_config_cjs = """module.exports = {
  parser: '@typescript-eslint/parser',
  rules: {
    'no-console': 'off'
  }
};"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "eslint.config.cjs":
                return eslint_config_cjs
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "eslint.config.cjs"
        assert result["content"] == eslint_config_cjs


def test_get_eslint_config_finds_in_package_json(base_args):
    package_json_content = """{
  "name": "test-package",
  "version": "1.0.0",
  "eslintConfig": {
    "rules": {
      "no-console": "error"
    }
  }
}"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "package.json":
                return package_json_content
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "package.json"

        config = json.loads(result["content"])
        assert config["rules"]["no-console"] == "error"


def test_get_eslint_config_package_json_without_eslint_config(base_args):
    package_json_content = """{
  "name": "test-package",
  "version": "1.0.0",
  "dependencies": {
    "eslint": "^8.0.0"
  }
}"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "package.json":
                return package_json_content
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_not_found(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        mock_get_raw.return_value = None

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_priority_order(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.js":
                return "module.exports = { rules: {} };"
            if file_path == "package.json":
                return '{"eslintConfig": {"rules": {}}}'
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.js"


def test_get_eslint_config_tries_all_config_files(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        mock_get_raw.return_value = None

        result = get_eslint_config(base_args)

        assert result is None
        assert mock_get_raw.call_count >= 8


def test_get_eslint_config_with_empty_package_json(base_args):
    package_json_content = "{}"

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "package.json":
                return package_json_content
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_with_complex_eslint_config_in_package_json(base_args):
    package_json_content = """{
  "name": "complex-package",
  "version": "2.0.0",
  "eslintConfig": {
    "parser": "@typescript-eslint/parser",
    "extends": [
      "eslint:recommended",
      "plugin:@typescript-eslint/recommended"
    ],
    "rules": {
      "no-console": "warn",
      "@typescript-eslint/no-unused-vars": "error"
    },
    "env": {
      "node": true,
      "es6": true
    }
  }
}"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "package.json":
                return package_json_content
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "package.json"

        config = json.loads(result["content"])
        assert config["parser"] == "@typescript-eslint/parser"
        assert "eslint:recommended" in config["extends"]
        assert config["rules"]["no-console"] == "warn"
        assert config["env"]["node"] is True


def test_get_eslint_config_handles_exception_gracefully(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        mock_get_raw.side_effect = Exception("Network error")

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_handles_json_decode_error(base_args):
    invalid_json = "{ invalid json content"

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == "package.json":
                return invalid_json
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_first_found_wins(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:

        def side_effect(owner, repo, file_path, ref, token):
            if file_path == ".eslintrc.json":
                return '{"rules": {"no-console": "error"}}'
            if file_path == ".eslintrc.js":
                return "module.exports = { rules: {} };"
            if file_path == ".eslintrc":
                return '{"rules": {}}'
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == ".eslintrc.json"


def test_get_eslint_config_skips_to_package_json_when_no_config_files(base_args):
    package_json_content = """{
  "name": "test-package",
  "eslintConfig": {
    "rules": {
      "no-console": "warn"
    }
  }
}"""

    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        call_count = 0

        def side_effect(owner, repo, file_path, ref, token):
            nonlocal call_count
            call_count += 1
            if file_path == "package.json":
                return package_json_content
            return None

        mock_get_raw.side_effect = side_effect

        result = get_eslint_config(base_args)

        assert result is not None
        assert result["filename"] == "package.json"
        assert call_count == 9
