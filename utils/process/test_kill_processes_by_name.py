# pylint: disable=unused-argument
import signal
from unittest.mock import patch

from utils.process.kill_processes_by_name import kill_processes_by_name


@patch("utils.process.kill_processes_by_name.time.sleep")
@patch("utils.process.kill_processes_by_name.os.path.exists", return_value=False)
@patch("utils.process.kill_processes_by_name.os.kill")
@patch("utils.process.kill_processes_by_name.read_local_file")
@patch("utils.process.kill_processes_by_name.os.listdir")
def test_kills_matching_process(
    mock_listdir, mock_read, mock_kill, _mock_exists, _mock_sleep
):
    mock_listdir.return_value = ["1", "12345", "self", "net"]
    mock_read.return_value = "/usr/bin/mongod\x00--port\x0034213"

    kill_processes_by_name("mongod")

    mock_kill.assert_any_call(12345, signal.SIGKILL)


@patch("utils.process.kill_processes_by_name.os.kill")
@patch("utils.process.kill_processes_by_name.read_local_file")
@patch("utils.process.kill_processes_by_name.os.listdir")
def test_skips_non_matching_process(mock_listdir, mock_read, mock_kill):
    mock_listdir.return_value = ["999"]
    mock_read.return_value = "/usr/bin/node\x00server.js"

    kill_processes_by_name("mongod")

    mock_kill.assert_not_called()


@patch("utils.process.kill_processes_by_name.os.listdir", side_effect=FileNotFoundError)
def test_skips_when_proc_missing(mock_listdir):
    # Should not raise on macOS where /proc doesn't exist
    kill_processes_by_name("mongod")


@patch("utils.process.kill_processes_by_name.os.kill")
@patch("utils.process.kill_processes_by_name.read_local_file", return_value=None)
@patch("utils.process.kill_processes_by_name.os.listdir")
def test_skips_when_cmdline_unreadable(mock_listdir, mock_read, mock_kill):
    mock_listdir.return_value = ["12345"]

    kill_processes_by_name("mongod")

    mock_kill.assert_not_called()


@patch("utils.process.kill_processes_by_name.time.sleep")
@patch("utils.process.kill_processes_by_name.os.path.exists")
@patch("utils.process.kill_processes_by_name.os.kill")
@patch("utils.process.kill_processes_by_name.read_local_file")
@patch("utils.process.kill_processes_by_name.os.listdir")
def test_waits_for_process_to_die(
    mock_listdir, mock_read, mock_kill, mock_exists, mock_sleep
):
    mock_listdir.return_value = ["42"]
    mock_read.return_value = "/usr/bin/mongod\x00--port\x0034213"
    # Process alive for 3 polls, then dies
    mock_exists.side_effect = [True, True, True, False]

    kill_processes_by_name("mongod")

    mock_kill.assert_any_call(42, signal.SIGKILL)
    assert mock_sleep.call_count == 3
