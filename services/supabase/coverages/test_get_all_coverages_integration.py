from services.supabase.coverages.get_all_coverages import get_all_coverages


def test_get_all_coverages_integration_with_nonexistent_repo():
    """Integration test: get_all_coverages with a repo_id that doesn't exist."""
    # Use a very large repo_id that's unlikely to exist
    nonexistent_repo_id = 999999999

    # Execute
    result = get_all_coverages(owner_id=789, repo_id=nonexistent_repo_id)

    # Verify - should return empty list for non-existent repo
    assert result == []


def test_get_all_coverages_integration_with_zero_repo_id():
    """Integration test: get_all_coverages with repo_id of 0."""
    # Execute
    result = get_all_coverages(owner_id=789, repo_id=0)

    # Verify - should return empty list for repo_id 0
    assert result == []


def test_get_all_coverages_integration_function_signature():
    """Integration test: verify the function can be called and returns expected types."""
    # Execute with a test repo_id
    result = get_all_coverages(owner_id=789, repo_id=1)

    # Verify - result should be a list
    assert isinstance(result, list)

    # All items should be dictionaries (Coverages objects)
    if result:
        assert all(isinstance(item, dict) for item in result)
