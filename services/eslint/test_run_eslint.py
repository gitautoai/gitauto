import subprocess
from unittest.mock import patch

from services.eslint.run_eslint import run_eslint


FOXQUILT_PACKAGE_JSON = """{
  "name": "foxcom-forms-backend",
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^5.9.1",
    "@typescript-eslint/parser": "^5.9.1",
    "eslint": "^7.22.0",
    "eslint-config-prettier": "^8.1.0",
    "eslint-import-resolver-typescript": "^4.4.4",
    "eslint-plugin-import": "^2.22.0",
    "eslint-plugin-prettier": "^3.3.1",
    "eslint-plugin-simple-import-sort": "^7.0.0"
  }
}"""

FOXQUILT_ESLINTRC = """{
  "parser": "@typescript-eslint/parser",
  "env": {
    "node": true
  },
  "parserOptions": {
    "ecmaVersion": 2020,
    "project": null,
    "sourceType": "module"
  },
  "extends": [
    "eslint:recommended"
  ],
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn",
    "simple-import-sort/exports": "error",
    "simple-import-sort/imports": "error"
  },
  "plugins": ["simple-import-sort"]
}"""


def test_run_eslint_fixes_import_sort():
    file_content = """import { z } from 'zod';
import { a } from 'aaa';

console.log(a, z);
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.ts",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content=FOXQUILT_PACKAGE_JSON,
    )

    assert result is not None
    assert "fixed_content" in result
    assert "import { a }" in result["fixed_content"]
    assert result["fixed_content"].index("import { a }") < result[
        "fixed_content"
    ].index("import { z }")


def test_run_eslint_detects_unused_vars():
    file_content = """const unused = 'test';

export const used = 'used';
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.ts",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content=FOXQUILT_PACKAGE_JSON,
    )

    assert result is not None
    assert result["success"] is False
    assert len(result["errors"]) > 0


def test_run_eslint_detects_console_warn():
    file_content = """console.log('test');

export const foo = 'bar';
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.ts",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content=FOXQUILT_PACKAGE_JSON,
    )

    assert result is not None
    assert len(result["errors"]) > 0
    assert any(
        "console" in str(err.get("message", "")).lower() for err in result["errors"]
    )


def test_run_eslint_with_valid_code():
    file_content = """export const foo = 'bar';
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.ts",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content=FOXQUILT_PACKAGE_JSON,
    )

    assert result is not None
    assert result["success"] is True
    assert len(result["errors"]) == 0


def test_run_eslint_skips_non_js_files():
    file_content = """def foo():
    pass
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.py",
        eslint_config_content=FOXQUILT_ESLINTRC,
    )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == file_content


def test_run_eslint_with_empty_content():
    result = run_eslint(
        file_content="",
        file_path="test.ts",
        eslint_config_content=FOXQUILT_ESLINTRC,
    )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == ""


def test_run_eslint_with_js_file():
    file_content = """const foo = 'bar';

export { foo };
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content=FOXQUILT_ESLINTRC,
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_jsx_file():
    file_content = """import React from 'react';

export const Component = () => <div>Test</div>;
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.jsx",
        eslint_config_content=FOXQUILT_ESLINTRC,
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_tsx_file():
    file_content = """import React from 'react';

export const Component: React.FC = () => <div>Test</div>;
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.tsx",
        eslint_config_content=FOXQUILT_ESLINTRC,
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_npm_install_failure():
    file_content = """export const foo = 'bar';
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content='{"devDependencies": {"eslint": "^7.22.0", "eslint-plugin-nonexistent": "^1.0.0"}}',
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_invalid_package_json():
    file_content = """export const foo = 'bar';
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content=FOXQUILT_ESLINTRC,
        package_json_content="invalid json{",
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_eslint_failure():
    file_content = """this is not valid javascript at all!!!
"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content='{"rules": {}}',
        package_json_content='{"devDependencies": {"eslint": "^7.22.0"}}',
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_js_module_exports_config():
    file_content = """export const foo = 'bar';
"""

    js_config = """module.exports = {
  rules: {
    'no-console': 'warn'
  }
};"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content=js_config,
        package_json_content='{"devDependencies": {"eslint": "^7.22.0"}}',
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_mjs_export_default_config():
    file_content = """export const foo = 'bar';
"""

    mjs_config = """export default {
  rules: {
    'no-console': 'warn'
  }
};"""

    result = run_eslint(
        file_content=file_content,
        file_path="test.js",
        eslint_config_content=mjs_config,
        package_json_content='{"devDependencies": {"eslint": "^7.22.0"}}',
    )

    assert result is not None
    assert "fixed_content" in result


def test_run_eslint_with_json_decode_error():
    file_content = """export const foo = 'bar';
"""

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not json output", stderr=""
        )
        mock_run.return_value = mock_result

        result = run_eslint(
            file_content=file_content,
            file_path="test.js",
            eslint_config_content='{"rules": {}}',
            package_json_content='{"devDependencies": {"eslint": "^7.22.0"}}',
        )

        assert result is not None
        assert result["success"] is True
        assert result["fixed_content"] == file_content


def test_run_eslint_with_fatal_error_return_code():
    file_content = """export const foo = 'bar';
"""

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="Fatal error"
        )
        mock_run.return_value = mock_result

        result = run_eslint(
            file_content=file_content,
            file_path="test.js",
            eslint_config_content='{"rules": {}}',
            package_json_content='{"devDependencies": {"eslint": "^7.22.0"}}',
        )

        assert result is not None
        assert result["success"] is False
        assert result["fixed_content"] == file_content
