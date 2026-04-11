# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.node.switch_node_version import switch_node_version


@patch("services.node.switch_node_version.run_subprocess")
def test_switches_version(mock_run):
    result = switch_node_version(version="20")
    assert result == "Switched to Node.js 20."
    mock_run.assert_called_once_with(["n", "20"], cwd="/tmp")


@patch("services.node.switch_node_version.run_subprocess")
def test_returns_default_on_failure(mock_run):
    mock_run.side_effect = ValueError("Command failed")
    result = switch_node_version(version="18")
    assert result == "Failed to switch Node.js version."
