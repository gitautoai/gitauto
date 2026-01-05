from services.efs.get_efs_dir import EFS_BASE, get_efs_dir


def test_get_efs_dir_returns_correct_path():
    result = get_efs_dir("owner", "repo")
    assert result == f"{EFS_BASE}/owner/repo"


def test_get_efs_dir_handles_special_characters():
    result = get_efs_dir("my-org", "my-repo-name")
    assert result == f"{EFS_BASE}/my-org/my-repo-name"
