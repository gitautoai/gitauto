from services.git.get_clone_dir import get_clone_dir


def test_get_clone_dir_with_pr_number():
    result = get_clone_dir("owner", "repo", 123)
    assert result == "/tmp/owner/repo/pr-123"


def test_get_clone_dir_without_pr_number():
    result = get_clone_dir("owner", "repo", None)
    assert result == "/tmp/owner/repo"
