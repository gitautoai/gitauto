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


def test_get_eslint_config_not_found(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        mock_get_raw.return_value = None

        result = get_eslint_config(base_args)

        assert result is None


def test_get_eslint_config_tries_all_config_files(base_args):
    with patch(
        "services.github.files.get_eslint_config.get_raw_content"
    ) as mock_get_raw:
        mock_get_raw.return_value = None

        result = get_eslint_config(base_args)

        assert result is None
        assert mock_get_raw.call_count >= 8
