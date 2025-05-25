# Standard imports
from unittest import mock

# Local imports
from services.supabase.coverages.upsert_coverages import CoverageItem, upsert_coverages


@mock.patch("services.supabase.coverages.upsert_coverages.supabase")
def test_filters_non_serializable_items(mock_supabase):
    # Setup mock supabase
    mock_result = mock.MagicMock()
    mock_result.data = [{"id": 1}]
    mock_execute = mock.MagicMock(return_value=mock_result)
    mock_upsert = mock.MagicMock(return_value=mock.MagicMock(execute=mock_execute))
    mock_supabase.table.return_value.upsert = mock_upsert
    mock_supabase.table.return_value.delete.return_value.eq.return_value.not_.in_.return_value.execute = (
        mock.MagicMock()
    )

    # Create a mix of valid and invalid items
    valid_item: CoverageItem = {
        "package_name": "test_package",
        "level": "file",
        "full_path": "path/to/valid/file.py",
        "line_coverage": 75.5,
        "statement_coverage": 80.0,
        "function_coverage": 90.0,
        "branch_coverage": 70.0,
        "path_coverage": 60.0,
        "uncovered_lines": "1,2,3",
        "uncovered_functions": "func1,func2",
        "uncovered_branches": "branch1,branch2",
    }

    # Non-serializable dictionary for testing (contains a non-serializable object)
    non_serializable_value = mock.MagicMock()
    non_serializable_value.__str__.return_value = "Non-serializable object"

    non_serializable_item: CoverageItem = {
        "package_name": "test_package",
        "level": "file",
        "full_path": "path/to/invalid/file.py",
        "line_coverage": 50.0,
        "statement_coverage": 60.0,
        "function_coverage": 70.0,
        "branch_coverage": 80.0,
        "path_coverage": 40.0,
        "uncovered_lines": "4,5,6",
        # This will cause JSON serialization to fail
        "uncovered_functions": non_serializable_value,
        "uncovered_branches": "branch3,branch4",
    }

    # Test with a mix of valid and invalid items
    coverages_list = [valid_item, non_serializable_item]

    # Test parameters
    owner_id = 123
    repo_id = 456
    branch_name = "main"
    primary_language = "python"
    user_name = "testuser"

    # Call the function
    result = upsert_coverages(
        coverages_list=coverages_list,
        owner_id=owner_id,
        repo_id=repo_id,
        branch_name=branch_name,
        primary_language=primary_language,
        user_name=user_name,
    )

    # Verify results
    assert result == [{"id": 1}]

    # Verify that only valid items were passed to upsert
    # Get the actual call arguments
    args, _kwargs = mock_upsert.call_args
    upserted_data = args[0]

    # Verify only one item was upserted (the valid one)
    assert len(upserted_data) == 1
    assert upserted_data[0]["full_path"] == "path/to/valid/file.py"


@mock.patch("services.supabase.coverages.upsert_coverages.supabase")
def test_returns_none_when_all_items_filtered(mock_supabase):
    # Setup mock supabase with proper chaining
    mock_delete_execute = mock.MagicMock()
    mock_eq = mock.MagicMock()
    mock_eq.execute = mock_delete_execute

    mock_delete = mock.MagicMock()
    mock_delete.eq.return_value = mock_eq

    mock_table = mock.MagicMock()
    mock_table.delete.return_value = mock_delete

    mock_supabase.table.return_value = mock_table

    # Create a list with only non-serializable items
    non_serializable_value = mock.MagicMock()
    non_serializable_value.__str__.return_value = "Non-serializable object"

    non_serializable_item: CoverageItem = {
        "package_name": "test_package",
        "level": "file",
        "full_path": "path/to/invalid/file.py",
        "line_coverage": 50.0,
        "statement_coverage": 60.0,
        "function_coverage": 70.0,
        "branch_coverage": 80.0,
        "path_coverage": 40.0,
        "uncovered_lines": non_serializable_value,  # Will cause JSON serialization to fail
        "uncovered_functions": "func3,func4",
        "uncovered_branches": "branch3,branch4",
    }

    # Test with only invalid items
    coverages_list = [non_serializable_item]

    # Test parameters
    owner_id = 123
    repo_id = 456
    branch_name = "main"
    primary_language = "python"
    user_name = "testuser"

    # Call the function
    result = upsert_coverages(
        coverages_list=coverages_list,
        owner_id=owner_id,
        repo_id=repo_id,
        branch_name=branch_name,
        primary_language=primary_language,
        user_name=user_name,
    )

    # Verify results
    assert result is None

    # Verify that upsert was not called
    mock_supabase.table.return_value.upsert.assert_not_called()

    # Verify that delete was called (to clean up files that no longer exist)
    mock_delete_execute.assert_called_once()


@mock.patch("services.supabase.coverages.upsert_coverages.supabase")
def test_sets_uncovered_fields_to_none_for_100_percent_coverage(mock_supabase):
    # Setup mock supabase
    mock_result = mock.MagicMock()
    mock_result.data = [{"id": 1}]
    mock_execute = mock.MagicMock(return_value=mock_result)
    mock_upsert = mock.MagicMock(return_value=mock.MagicMock(execute=mock_execute))
    mock_supabase.table.return_value.upsert = mock_upsert
    mock_supabase.table.return_value.delete.return_value.eq.return_value.not_.in_.return_value.execute = (
        mock.MagicMock()
    )

    # Create an item with 100% coverage
    full_coverage_item: CoverageItem = {
        "package_name": "test_package",
        "level": "file",
        "full_path": "path/to/full/coverage.py",
        "line_coverage": 100.0,
        "statement_coverage": 100.0,
        "function_coverage": 100.0,
        "branch_coverage": 100.0,
        "path_coverage": 100.0,
        "uncovered_lines": "This should be set to None",
        "uncovered_functions": "This should be set to None",
        "uncovered_branches": "This should be set to None",
    }

    # Test parameters
    owner_id = 123
    repo_id = 456
    branch_name = "main"
    primary_language = "python"
    user_name = "testuser"

    # Call the function
    result = upsert_coverages(
        coverages_list=[full_coverage_item],
        owner_id=owner_id,
        repo_id=repo_id,
        branch_name=branch_name,
        primary_language=primary_language,
        user_name=user_name,
    )

    # Verify results
    assert result == [{"id": 1}]

    # Verify that uncovered fields were set to None
    args, _kwargs = mock_upsert.call_args
    upserted_data = args[0]

    assert len(upserted_data) == 1
    assert upserted_data[0]["uncovered_lines"] is None
    assert upserted_data[0]["uncovered_functions"] is None
    assert upserted_data[0]["uncovered_branches"] is None
