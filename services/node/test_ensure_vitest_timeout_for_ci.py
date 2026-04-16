# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.node.ensure_vitest_timeout_for_ci import ensure_vitest_timeout_for_ci


@pytest.fixture()
def mock_read_local_file():
    with patch("services.node.ensure_vitest_timeout_for_ci.read_local_file") as mock:
        yield mock


@pytest.fixture()
def mock_write_and_commit():
    with patch(
        "services.node.ensure_vitest_timeout_for_ci.write_and_commit_file"
    ) as mock:
        mock.return_value = MagicMock(spec=FileWriteResult, success=True)
        yield mock


def test_no_vitest_config_file(mock_read_local_file: MagicMock, create_test_base_args):
    base_args = create_test_base_args()
    result = ensure_vitest_timeout_for_ci(
        root_files=["package.json", "README.md"], base_args=base_args
    )
    assert result is None
    mock_read_local_file.assert_not_called()


def test_already_has_test_timeout(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    mock_read_local_file.return_value = (
        "export default defineConfig({\n  test: {\n    testTimeout: 10000,\n  },\n});\n"
    )
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_empty_content(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    mock_read_local_file.return_value = ""
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_no_test_block(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    mock_read_local_file.return_value = (
        "export default defineConfig({\n  plugins: [],\n});\n"
    )
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result is None
    mock_write_and_commit.assert_not_called()


def test_injects_into_test_block(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    config = "export default defineConfig({\n  test: {\n    name: 'unit',\n  },\n});\n"
    mock_read_local_file.return_value = config
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result == "vitest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("name: 'unit'")


def test_preserves_indentation(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    config = "export default defineConfig({\n    test: {\n        name: 'unit',\n    },\n});\n"
    mock_read_local_file.return_value = config
    ensure_vitest_timeout_for_ci(root_files=["vitest.config.ts"], base_args=base_args)
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "\n        testTimeout: process.env.CI ? 180000 : 5000," in written


def test_write_failure(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    config = "export default defineConfig({\n  test: {\n    name: 'unit',\n  },\n});\n"
    mock_read_local_file.return_value = config
    mock_write_and_commit.return_value = MagicMock(spec=FileWriteResult, success=False)
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result is None


# --- Real-world configs ---


WEBSITE_VITEST_CONFIG = """import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { playwright } from '@vitest/browser-playwright';
import { defineConfig } from 'vitest/config';

import { storybookTest } from '@storybook/addon-vitest/vitest-plugin';

const dirname =
  typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    storybookTest({ configDir: path.join(dirname, '.storybook') }),
  ],
  test: {
    name: 'storybook',
    browser: {
      enabled: true,
      headless: true,
      provider: playwright(),
      instances: [{ browser: 'chromium' }],
    },
    setupFiles: ['.storybook/vitest.setup.ts'],
  },
});
"""


def test_website_vitest(
    mock_read_local_file: MagicMock,
    mock_write_and_commit: MagicMock,
    create_test_base_args,
):
    base_args = create_test_base_args()
    mock_read_local_file.return_value = WEBSITE_VITEST_CONFIG
    result = ensure_vitest_timeout_for_ci(
        root_files=["vitest.config.ts"], base_args=base_args
    )
    assert result == "vitest.config.ts"
    written = mock_write_and_commit.call_args.kwargs["file_content"]
    assert "testTimeout: process.env.CI ? 180000 : 5000," in written
    assert written.index("testTimeout") < written.index("name: 'storybook'")
