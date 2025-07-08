import pytest
from unittest.mock import patch

from services.github.utils.create_permission_url import create_permission_url


def test_create_permission_url_for_organization():
    """Test that create_permission_url returns correct URL for Organization owner type."""
    owner_type = "Organization"
    owner_name = "test-org"
    installation_id = 12345
    
    result = create_permission_url(owner_type, owner_name, installation_id)
    
    expected = "https://github.com/organizations/test-org/settings/installations/12345/permissions/update"
    assert result == expected


def test_create_permission_url_for_user():
    """Test that create_permission_url returns correct URL for User owner type."""
    owner_type = "User"
    owner_name = "test-user"
    installation_id = 67890
    
    result = create_permission_url(owner_type, owner_name, installation_id)
    
    expected = "https://github.com/settings/installations/67890/permissions/update"
    assert result == expected


def test_create_permission_url_with_different_installation_ids():
    """Test that create_permission_url handles different installation IDs correctly."""
    owner_type = "Organization"
    owner_name = "example-org"
    
    # Test with various installation IDs
    test_cases = [1, 999, 123456789, 0]
    
    for installation_id in test_cases:
        result = create_permission_url(owner_type, owner_name, installation_id)
        expected = f"https://github.com/organizations/example-org/settings/installations/{installation_id}/permissions/update"
        assert result == expected


def test_create_permission_url_with_different_owner_names():
    """Test that create_permission_url handles different owner names correctly."""
    owner_type = "Organization"
    installation_id = 12345
    
    # Test with various owner names
    test_cases = ["org", "my-organization", "test_org_123", "ORG-NAME"]
    
    for owner_name in test_cases:
        result = create_permission_url(owner_type, owner_name, installation_id)
        expected = f"https://github.com/organizations/{owner_name}/settings/installations/{installation_id}/permissions/update"
        assert result == expected


def test_create_permission_url_user_ignores_owner_name():
    """Test that create_permission_url ignores owner_name for User owner type."""
    owner_type = "User"
    installation_id = 54321
    
    # Test with different owner names - they should all produce the same result for User type
    test_names = ["user1", "user2", "different-user", ""]
    
    expected = "https://github.com/settings/installations/54321/permissions/update"
    
    for owner_name in test_names:
        result = create_permission_url(owner_type, owner_name, installation_id)
        assert result == expected


@patch('services.github.utils.create_permission_url.GH_BASE_URL', 'https://custom-github.com')
def test_create_permission_url_with_custom_base_url():
    """Test that create_permission_url uses the configured base URL."""
    owner_type = "Organization"
    owner_name = "test-org"
    installation_id = 12345
    
    result = create_permission_url(owner_type, owner_name, installation_id)
    
    expected = "https://custom-github.com/organizations/test-org/settings/installations/12345/permissions/update"
    assert result == expected


@pytest.mark.parametrize("owner_type,owner_name,installation_id,expected", [
    ("Organization", "github", 1, "https://github.com/organizations/github/settings/installations/1/permissions/update"),
    ("User", "octocat", 2, "https://github.com/settings/installations/2/permissions/update"),
    ("Organization", "microsoft", 999999, "https://github.com/organizations/microsoft/settings/installations/999999/permissions/update"),
    ("User", "torvalds", 123, "https://github.com/settings/installations/123/permissions/update"),
])
def test_create_permission_url_parametrized(owner_type, owner_name, installation_id, expected):
    """Test create_permission_url with various parameter combinations."""
    result = create_permission_url(owner_type, owner_name, installation_id)
    assert result == expected


def test_create_permission_url_return_type():
    """Test that create_permission_url returns a string."""
    result = create_permission_url("Organization", "test", 123)
    assert isinstance(result, str)
    
    result = create_permission_url("User", "test", 456)
    assert isinstance(result, str)


def test_create_permission_url_url_structure():
    """Test that create_permission_url returns properly formatted URLs."""
    # Test Organization URL structure
    org_result = create_permission_url("Organization", "test-org", 123)
    assert org_result.startswith("https://github.com/organizations/")
    assert "/settings/installations/" in org_result
    assert org_result.endswith("/permissions/update")
    
    # Test User URL structure
    user_result = create_permission_url("User", "test-user", 456)
    assert user_result.startswith("https://github.com/settings/installations/")
    assert user_result.endswith("/permissions/update")
    assert "/organizations/" not in user_result
