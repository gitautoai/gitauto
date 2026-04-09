# pylint: disable=redefined-outer-name,unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.node.ensure_jest_timeout_for_ci import ensure_jest_timeout_for_ci
from services.types.base_args import BaseArgs

BASE_ARGS = cast(
    BaseArgs,
    {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
        "clone_dir": "/tmp/test",
    },
)


@pytest.fixture()
def mock_read_local_file():
    with patch("services.node.ensure_jest_timeout_for_ci.read_local_file") as mock:
        yield mock


@pytest.fixture()
def mock_write_and_commit():
    with patch(
        "services.node.ensure_jest_timeout_for_ci.write_and_commit_file"
    ) as mock:
        mock.return_value = MagicMock(spec=FileWriteResult, success=True)
        yield mock


def test_no_jest_config_file(mock_read_local_file: MagicMock):
    result = ensure_jest_timeout_for_ci(
        root_files=["package.json", "README.md"], base_args=BASE_ARGS
    )
    assert result is None
    mock_read_local_file.assert_not_called()


def test_already_has_correct_timeout(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = (
        "module.exports = {\n  testTimeout: process.env.CI ? 180000 : 5000,\n};\n"
    )
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_updates_wrong_timeout_value(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = (
        "module.exports = {\n  testTimeout: 10000,\n};\n"
    )
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "180000" in written
    assert "10000" not in written


def test_empty_content(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = ""
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_injects_into_module_exports(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = (
        "module.exports = {\n  preset: 'ts-jest',\n  testEnvironment: 'jsdom',\n};\n"
    )
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written_content = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written_content
    assert written_content.index("testTimeout") < written_content.index("preset")


def test_injects_into_export_default(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = "export default {\n  preset: 'ts-jest',\n};\n"
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written_content = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written_content


def test_injects_into_typed_config(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    config = "import type { Config } from 'jest';\nconst config: Config = {\n  preset: 'ts-jest',\n};\nexport default config;\n"
    mock_read_local_file.return_value = config
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written_content = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written_content


def test_preserves_indentation(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = (
        "module.exports = {\n    preset: 'ts-jest',\n};\n"
    )
    ensure_jest_timeout_for_ci(root_files=["jest.config.js"], base_args=BASE_ARGS)
    written_content = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "\n    testTimeout: process.env.CI ? 180000 : 5000," in written_content


def test_no_matching_pattern(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = "const x = 42;\n"
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_write_failure(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = "module.exports = {\n  preset: 'ts-jest',\n};\n"
    mock_write_and_commit.return_value = MagicMock(spec=FileWriteResult, success=False)
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result is None


def test_prefers_first_config_file(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = "module.exports = {\n  preset: 'ts-jest',\n};\n"
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js", "jest.config.ts"],
        base_args=BASE_ARGS,
    )
    assert result == "jest.config.js"


# --- Real-world configs ---


FOXCOM_FORMS_CONFIG = (
    "module.exports = {\n  setupFiles: ['jest-launchdarkly-mock']\n};\n"
)

FOXDEN_ADMIN_PORTAL_CONFIG = """export default {
  clearMocks: true,
  coverageDirectory: 'coverage',
  collectCoverageFrom: ['<rootDir>/src/**/*.ts'],
  coverageProvider: 'v8',
  setupFilesAfterEnv: ['<rootDir>/test/setupTests.ts'],
  testEnvironment: 'jsdom',
  testMatch: ['**/__tests__/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[tj]s?(x)']
};
"""

FOXDEN_VERSION_CONTROLLER_CONFIG = """import jestMongoDbPreset from '@shelf/jest-mongodb/jest-preset.js';
import merge from 'merge';
import tsJestPreset from 'ts-jest/jest-preset.js';

export default merge.recursive(tsJestPreset, jestMongoDbPreset, {
  clearMocks: true,
  collectCoverage: true,
  collectCoverageFrom: ['<rootDir>/src/**/*.ts'],
  coverageDirectory: 'coverage',
  maxWorkers: 1,
  testEnvironment: 'node',
  testMatch: ['**/test/**/*.spec.ts'],
  verbose: true,
});
"""

FOXDEN_RATING_QUOTING_CONFIG = """module.exports = {
  collectCoverage: true,
  collectCoverageFrom: ['<rootDir>/src/**/*.ts'],
  maxWorkers: 1,
  verbose: true,
  testTimeout: 60000,
  projects: [
    {
      displayName: 'unit',
      preset: 'ts-jest',
      testEnvironment: 'node',
      testMatch: ['<rootDir>/src/**/*.test.ts'],
    },
  ]
};
"""

FOXCOM_FORMS_BACKEND_CONFIG = """module.exports = {
  collectCoverage: true,
  collectCoverageFrom: ['<rootDir>/src/**/*.ts'],
  globalSetup: '<rootDir>/test/setup.ts',
  globalTeardown: '<rootDir>/test/teardown.ts',
  maxWorkers: 1,
  preset: 'ts-jest',
  testEnvironment: 'node',
  verbose: true,
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }],
    '\\.handlebars$': 'jest-transform-stub'
  },
  restoreMocks: true
};
"""

FOXDEN_AUTH_SERVICE_CONFIG = """/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
export default {
  clearMocks: true,
  collectCoverage: true,
  collectCoverageFrom: ['./src/**/*.ts'],
  coverageDirectory: 'coverage',
  coverageProvider: 'v8',
  globalSetup: '<rootDir>/test/setup.ts',
  globalTeardown: '<rootDir>/test/teardown.ts',
  maxWorkers: '1',
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.eslint.json' }],
  },
  restoreMocks: true,
  setupFilesAfterEnv: ['<rootDir>/test/mongo-client.ts'],
  testEnvironment: 'node',
  testMatch: ['<rootDir>/test/spec/**/*.spec.ts'],
};
"""


def test_foxcom_forms(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXCOM_FORMS_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("setupFiles")


def test_foxden_admin_portal(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("clearMocks")


def test_foxden_version_controller_merge_recursive(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_VERSION_CONTROLLER_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("clearMocks")


def test_foxden_rating_quoting_updates_wrong_timeout(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_RATING_QUOTING_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert "60000" not in written


def test_foxcom_forms_backend(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXCOM_FORMS_BACKEND_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("collectCoverage")


def test_foxden_auth_service(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_AUTH_SERVICE_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("clearMocks")


# Config with duplicate testTimeout (last-key-wins bug from parallel PR merges)
FOXDEN_ADMIN_PORTAL_DUPLICATE_TIMEOUT = """export default {
  testTimeout: process.env.CI ? 180000 : 5000,
  clearMocks: true,
  coverageDirectory: 'coverage',
  collectCoverageFrom: ['<rootDir>/src/**/*.ts'],
  coverageProvider: 'v8',
  setupFilesAfterEnv: ['<rootDir>/test/setupTests.ts'],
  testEnvironment: 'jsdom',
  testMatch: ['**/__tests__/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[tj]s?(x)'],

  testTimeout: process.env.CI ? 30000 : 5000
};
"""


def test_removes_duplicate_test_timeout_keeps_first(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_DUPLICATE_TIMEOUT
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    # Should keep first (180000) and remove second (30000)
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert "testTimeout: process.env.CI ? 30000 : 5000" not in written
    # Should only have one testTimeout
    assert written.count("testTimeout") == 1


WEBSITE_JEST_CONFIG = """import type { Config } from "jest";
import nextJest from "next/jest";

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig: Config = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  testPathIgnorePatterns: ["/node_modules/", "/e2e/", "\\\\.integration\\\\.test\\\\."],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  testMatch: ["**/__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"],
  collectCoverage: false,
};

export default createJestConfig(customJestConfig);
"""


def test_website_next_jest(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = WEBSITE_JEST_CONFIG
    result = ensure_jest_timeout_for_ci(
        root_files=["jest.config.ts"], base_args=BASE_ARGS
    )
    assert result == "jest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("setupFilesAfterEnv")


# --- Real-world craco configs (foxden-admin-portal) ---

# Original craco.config.js before GitAuto fix — missing testTimeout entirely
FOXDEN_ADMIN_PORTAL_CRACO_NO_TIMEOUT = """module.exports = {
  style: {
    postcss: {
      plugins: [require('tailwindcss'), require('autoprefixer')]
    }
  },
  jest: {
    configure: {
      roots: ['<rootDir>/src', '<rootDir>/test'],
      testMatch: ['<rootDir>/test/**/*.{spec,test}.{js,jsx,ts,tsx}'],
      setupFilesAfterSetup: ['<rootDir>/test/setupTests.ts'],
      testEnvironment: 'jsdom',
      moduleNameMapper: {
        '\\\\.(css|less|scss|sass)$': '<rootDir>/test/__mocks__/styleMock.js'
      }
    }
  }
};
"""

# After fix — testTimeout present with sufficient value
FOXDEN_ADMIN_PORTAL_CRACO_WITH_TIMEOUT = """module.exports = {
  style: {
    postcss: {
      plugins: [require('tailwindcss'), require('autoprefixer')]
    }
  },
  jest: {
    configure: {
      testTimeout: process.env.CI ? 180000 : 5000,
      roots: ['<rootDir>/src', '<rootDir>/test'],
      testMatch: ['<rootDir>/test/**/*.{spec,test}.{js,jsx,ts,tsx}'],
      setupFilesAfterSetup: ['<rootDir>/test/setupTests.ts'],
      testEnvironment: 'jsdom',
      moduleNameMapper: {
        '\\\\.(css|less|scss|sass)$': '<rootDir>/test/__mocks__/styleMock.js'
      }
    }
  }
};
"""

# Craco config with testTimeout set too low
FOXDEN_ADMIN_PORTAL_CRACO_LOW_TIMEOUT = """module.exports = {
  style: {
    postcss: {
      plugins: [require('tailwindcss'), require('autoprefixer')]
    }
  },
  jest: {
    configure: {
      testTimeout: 10000,
      roots: ['<rootDir>/src', '<rootDir>/test'],
      testEnvironment: 'jsdom'
    }
  }
};
"""

# Craco config without any jest section
CRACO_NO_JEST_SECTION = """module.exports = {
  style: {
    postcss: {
      plugins: [require('tailwindcss'), require('autoprefixer')]
    }
  }
};
"""


def test_craco_injects_timeout_into_configure_block(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_CRACO_NO_TIMEOUT
    result = ensure_jest_timeout_for_ci(
        root_files=["craco.config.js", "package.json"], base_args=BASE_ARGS
    )
    assert result == "craco.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    # testTimeout should appear INSIDE configure block, before roots
    assert written.index("testTimeout") < written.index("roots")
    assert written.index("testTimeout") > written.index("configure")


def test_craco_already_has_correct_timeout(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_CRACO_WITH_TIMEOUT
    result = ensure_jest_timeout_for_ci(
        root_files=["craco.config.js"], base_args=BASE_ARGS
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_craco_updates_low_timeout(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_CRACO_LOW_TIMEOUT
    result = ensure_jest_timeout_for_ci(
        root_files=["craco.config.js"], base_args=BASE_ARGS
    )
    assert result == "craco.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert "10000" not in written


def test_craco_takes_priority_over_jest_config(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    mock_read_local_file.return_value = FOXDEN_ADMIN_PORTAL_CRACO_NO_TIMEOUT
    result = ensure_jest_timeout_for_ci(
        root_files=["craco.config.js", "jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "craco.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written


def test_craco_without_jest_section_falls_through_to_jest_config(
    mock_read_local_file: MagicMock, mock_write_and_commit: MagicMock
):
    jest_config = "module.exports = {\n  preset: 'ts-jest',\n};\n"

    def side_effect(file_path, base_dir):
        if file_path == "craco.config.js":
            return CRACO_NO_JEST_SECTION
        if file_path == "jest.config.js":
            return jest_config
        return None

    mock_read_local_file.side_effect = side_effect
    result = ensure_jest_timeout_for_ci(
        root_files=["craco.config.js", "jest.config.js"], base_args=BASE_ARGS
    )
    assert result == "jest.config.js"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
