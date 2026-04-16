# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from unittest.mock import patch

from services.prettier.get_prettier_config import get_prettier_config


def test_get_prettier_config_finds_prettierrc(create_test_base_args):
    base_args = create_test_base_args()
    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == ".prettierrc":
                return '{"semi": false}'
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == ".prettierrc"
        assert result["content"] == '{"semi": false}'


def test_get_prettier_config_finds_prettierrc_json(create_test_base_args):
    base_args = create_test_base_args()
    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == ".prettierrc.json":
                return '{"tabWidth": 4}'
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == ".prettierrc.json"


def test_get_prettier_config_finds_prettierrc_js(create_test_base_args):
    base_args = create_test_base_args()
    prettierrc_js = "module.exports = { semi: false };"

    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == ".prettierrc.js":
                return prettierrc_js
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == ".prettierrc.js"
        assert result["content"] == prettierrc_js


def test_get_prettier_config_finds_prettier_config_js(create_test_base_args):
    base_args = create_test_base_args()
    config_js = "export default { semi: true };"

    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == "prettier.config.js":
                return config_js
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == "prettier.config.js"


def test_get_prettier_config_finds_in_package_json(create_test_base_args):
    base_args = create_test_base_args()
    package_json_content = """{
  "name": "test-package",
  "version": "1.0.0",
  "prettier": {
    "semi": false,
    "tabWidth": 2
  }
}"""

    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == "package.json":
                return package_json_content
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == "package.json"

        config = json.loads(result["content"])
        assert config["semi"] is False
        assert config["tabWidth"] == 2


def test_get_prettier_config_package_json_without_prettier(create_test_base_args):
    base_args = create_test_base_args()
    package_json_content = """{
  "name": "test-package",
  "version": "1.0.0",
  "dependencies": {
    "prettier": "^3.0.0"
  }
}"""

    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == "package.json":
                return package_json_content
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is None


def test_get_prettier_config_not_found(create_test_base_args):
    base_args = create_test_base_args()
    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:
        mock_read.return_value = None

        result = get_prettier_config(base_args)

        assert result is None


def test_get_prettier_config_priority_order(create_test_base_args):
    base_args = create_test_base_args()
    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == ".prettierrc":
                return '{"semi": false}'
            if file_name == "package.json":
                return '{"prettier": {"semi": true}}'
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is not None
        assert result["filename"] == ".prettierrc"


def test_get_prettier_config_handles_exception_gracefully(create_test_base_args):
    base_args = create_test_base_args()
    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:
        mock_read.side_effect = Exception("Network error")

        result = get_prettier_config(base_args)

        assert result is None


def test_get_prettier_config_handles_json_decode_error(create_test_base_args):
    base_args = create_test_base_args()
    invalid_json = "{ invalid json content"

    with patch("services.prettier.get_prettier_config.read_local_file") as mock_read:

        def side_effect(file_name, **kwargs):
            if file_name == "package.json":
                return invalid_json
            return None

        mock_read.side_effect = side_effect

        result = get_prettier_config(base_args)

        assert result is None
