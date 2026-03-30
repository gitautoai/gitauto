from utils.logs.save_ci_log_to_file import CI_LOG_PATH, save_ci_log_to_file


def test_saves_log_to_file(tmp_path):
    log_content = "Error: test failed\nExpected 1 but got 2"
    save_ci_log_to_file(str(tmp_path), log_content)

    full_path = tmp_path / CI_LOG_PATH
    assert full_path.exists()
    assert full_path.read_text() == log_content


def test_creates_gitauto_dir(tmp_path):
    save_ci_log_to_file(str(tmp_path), "some log")
    assert (tmp_path / ".gitauto").is_dir()


def test_overwrites_existing_file(tmp_path):
    save_ci_log_to_file(str(tmp_path), "first log")
    save_ci_log_to_file(str(tmp_path), "second log")

    full_path = tmp_path / CI_LOG_PATH
    assert full_path.read_text() == "second log"


def test_handles_large_log(tmp_path):
    large_log = "x" * 500_000
    save_ci_log_to_file(str(tmp_path), large_log)

    full_path = tmp_path / CI_LOG_PATH
    assert len(full_path.read_text()) == 500_000
