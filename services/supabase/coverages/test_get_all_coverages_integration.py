from services.supabase.coverages.get_all_coverages import get_all_coverages


def test_get_all_coverages_integration_with_nonexistent_repo():
    """Integration test: get_all_coverages with a repo_id that doesn't exist."""
    # Use a very large repo_id that's unlikely to exist
    nonexistent_repo_id = 999999999

    # Execute
    result = get_all_coverages(repo_id=nonexistent_repo_id)

    # Verify - should return None for non-existent repo
    assert result is None


def test_get_all_coverages_integration_with_zero_repo_id():
    """Integration test: get_all_coverages with repo_id of 0."""
    # Execute
    result = get_all_coverages(repo_id=0)

    # Verify - should return None for repo_id 0
    assert result is None


def test_get_all_coverages_integration_function_signature():
    """Integration test: verify the function can be called and returns expected types."""
    # Execute with a test repo_id
    result = get_all_coverages(repo_id=1)

    # Verify - result should be either None or a list
    assert result is None or isinstance(result, list)

    # If result is a list, all items should be dictionaries (Coverages objects)
    if result is not None:
        assert all(isinstance(item, dict) for item in result)
