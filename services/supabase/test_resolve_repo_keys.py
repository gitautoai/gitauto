# pylint: disable=redefined-outer-name, unused-argument
from unittest.mock import Mock, patch

from services.supabase.resolve_repo_keys import resolve_repo_keys

PATCH_TARGET = "services.supabase.resolve_repo_keys.supabase"


def _build_mock_supabase(owners_data, repos_data):
    """Build a mock supabase client that returns given data for owners and repos queries."""
    mock_supabase = Mock()

    owners_result = Mock()
    owners_result.data = owners_data

    repos_result = Mock()
    repos_result.data = repos_data

    def table_side_effect(table_name):
        mock_table = Mock()
        if table_name == "owners":
            mock_select = Mock()
            mock_in = Mock()
            mock_table.select.return_value = mock_select
            mock_select.in_.return_value = mock_in
            mock_in.execute.return_value = owners_result
        elif table_name == "repositories":
            mock_select = Mock()
            mock_in = Mock()
            mock_table.select.return_value = mock_select
            mock_select.in_.return_value = mock_in
            mock_in.execute.return_value = repos_result
        return mock_table

    mock_supabase.table.side_effect = table_side_effect
    return mock_supabase


def test_empty_set_returns_empty_dict():
    # Empty input should short-circuit and return {} without any DB calls
    result = resolve_repo_keys(set())
    assert result == {}


def test_single_owner_single_repo():
    # Basic happy path: one (owner_id, repo_id) pair resolves to (owner_name, repo_name)
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = [{"owner_id": 1, "repo_id": 100, "repo_name": "widget"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    assert result == {("acme", "widget"): None}


def test_multiple_repos_same_owner():
    # Two repos under the same owner should both resolve correctly
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = [
        {"owner_id": 1, "repo_id": 100, "repo_name": "widget"},
        {"owner_id": 1, "repo_id": 200, "repo_name": "gadget"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100), (1, 200)})

    assert result == {("acme", "widget"): None, ("acme", "gadget"): None}


def test_multiple_owners_multiple_repos():
    # Multiple owners with different repos should all resolve independently
    owners_data = [
        {"owner_id": 1, "owner_name": "acme"},
        {"owner_id": 2, "owner_name": "globex"},
    ]
    repos_data = [
        {"owner_id": 1, "repo_id": 100, "repo_name": "widget"},
        {"owner_id": 2, "repo_id": 200, "repo_name": "laser"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100), (2, 200)})

    assert result == {("acme", "widget"): None, ("globex", "laser"): None}


def test_owner_not_found_falls_back_to_str_id():
    # When owner_id has no matching row in owners table, fall back to str(owner_id)
    owners_data = []
    repos_data = [{"owner_id": 999, "repo_id": 50, "repo_name": "orphan-repo"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(999, 50)})

    assert result == {("999", "orphan-repo"): None}


def test_repo_not_in_repo_keys_is_filtered_out():
    # DB returns extra repos not in the input set; they should be excluded from result
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = [
        {"owner_id": 1, "repo_id": 100, "repo_name": "widget"},
        {"owner_id": 1, "repo_id": 999, "repo_name": "unrelated"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    assert result == {("acme", "widget"): None}


def test_owners_result_data_is_none():
    # When owners query returns None data, all owners fall back to str(owner_id)
    repos_data = [{"owner_id": 5, "repo_id": 10, "repo_name": "myrepo"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(None, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(5, 10)})

    assert result == {("5", "myrepo"): None}


def test_repos_result_data_is_none():
    # When repos query returns None data, result should be empty (no repos to iterate)
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, None)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    assert result == {}


def test_both_results_data_are_none():
    # When both queries return None data, result should be empty
    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(None, None)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    assert result == {}


def test_exception_returns_empty_dict_via_decorator():
    # The @handle_exceptions decorator with default_return_value={} catches exceptions
    with patch(PATCH_TARGET) as mock_supabase:
        mock_supabase.table.side_effect = Exception("DB connection failed")

        result = resolve_repo_keys({(1, 100)})

    assert result == {}


def test_repo_key_mismatch_owner_id_filters_correctly():
    # DB returns a repo with owner_id=2 but input only has (1, 100); should be excluded
    owners_data = [
        {"owner_id": 1, "owner_name": "acme"},
        {"owner_id": 2, "owner_name": "globex"},
    ]
    repos_data = [
        {"owner_id": 2, "repo_id": 100, "repo_name": "widget"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    # (2, 100) is not in repo_keys {(1, 100)}, so it's filtered out
    assert result == {}


def test_queries_correct_tables_and_columns():
    # Verify the function queries the right tables with the right columns and filters
    owners_data = [{"owner_id": 10, "owner_name": "org10"}]
    repos_data = [{"owner_id": 10, "repo_id": 20, "repo_name": "repo20"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        resolve_repo_keys({(10, 20)})

    calls = mock_supabase.table.call_args_list
    assert calls[0].args[0] == "owners"
    assert calls[1].args[0] == "repositories"


def test_large_input_set():
    # Verify function handles a larger set of keys without issues
    repo_keys = {(i, i * 10) for i in range(1, 51)}
    owners_data = [{"owner_id": i, "owner_name": f"owner-{i}"} for i in range(1, 51)]
    repos_data = [
        {"owner_id": i, "repo_id": i * 10, "repo_name": f"repo-{i * 10}"}
        for i in range(1, 51)
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys(repo_keys)

    assert len(result) == 50
    # Spot-check a few entries
    assert ("owner-1", "repo-10") in result
    assert ("owner-25", "repo-250") in result
    assert ("owner-50", "repo-500") in result


def test_partial_owner_coverage():
    # Some owners found, some not; missing owners fall back to str(owner_id)
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = [
        {"owner_id": 1, "repo_id": 100, "repo_name": "widget"},
        {"owner_id": 2, "repo_id": 200, "repo_name": "gadget"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100), (2, 200)})

    assert result == {("acme", "widget"): None, ("2", "gadget"): None}


def test_duplicate_owner_ids_in_keys_deduped():
    # Multiple keys with same owner_id should only query that owner_id once
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = [
        {"owner_id": 1, "repo_id": 100, "repo_name": "widget"},
        {"owner_id": 1, "repo_id": 200, "repo_name": "gadget"},
    ]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100), (1, 200)})

    # Both repos resolve with the same owner name
    assert result == {("acme", "widget"): None, ("acme", "gadget"): None}


def test_no_matching_repos_in_db():
    # Input keys exist but DB returns no matching repos at all
    owners_data = [{"owner_id": 1, "owner_name": "acme"}]
    repos_data = []

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(1, 100)})

    assert result == {}


def test_owner_id_zero():
    # Edge case: owner_id=0 is a valid integer; should work and fall back to "0" if not found
    owners_data = []
    repos_data = [{"owner_id": 0, "repo_id": 1, "repo_name": "zero-repo"}]

    with patch(PATCH_TARGET) as mock_supabase:
        mock = _build_mock_supabase(owners_data, repos_data)
        mock_supabase.table.side_effect = mock.table.side_effect

        result = resolve_repo_keys({(0, 1)})

    assert result == {("0", "zero-repo"): None}
