from services.git.get_clone_url import get_clone_url


def test_get_clone_url_basic():
    result = get_clone_url("owner", "repo", "token123")
    assert result == "https://x-access-token:token123@github.com/owner/repo.git"


def test_get_clone_url_with_special_characters_in_token():
    result = get_clone_url("owner", "repo", "ghs_abc123XYZ")
    assert result == "https://x-access-token:ghs_abc123XYZ@github.com/owner/repo.git"


def test_get_clone_url_with_org_name():
    result = get_clone_url("my-org", "my-repo", "token")
    assert result == "https://x-access-token:token@github.com/my-org/my-repo.git"
