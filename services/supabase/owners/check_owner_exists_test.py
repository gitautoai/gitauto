

@pytest.mark.parametrize("owner_id,expected_data,expected_result", [
    (123, [{"owner_id": 123}], True),
    (456, [], False),
    (789, [{"owner_id": 789}, {"owner_id": 999}], True),  # Multiple results still True
    (0, [], False),
    (-1, [], False),
    (999999, [{"owner_id": 999999}], True),
])
def test_check_owner_exists_with_various_scenarios(mock_supabase_client, owner_id, expected_data, expected_result):
    """Test check_owner_exists with various owner IDs and data scenarios."""
    # Mock the supabase query chain
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    
    # Mock execute to return the expected data
    mock_eq.execute.return_value = (None, expected_data)
    
    result = check_owner_exists(owner_id)
    
    assert result is expected_result
    mock_supabase_client.table.assert_called_with(table_name="owners")
    mock_table.select.assert_called_with("owner_id")
    mock_select.eq.assert_called_with(column="owner_id", value=owner_id)
    mock_eq.execute.assert_called_once()


def test_check_owner_exists_exception_handling_returns_default():
    """Test that check_owner_exists returns False when an exception occurs."""
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock_supabase:
        # Make supabase.table raise an exception
        mock_supabase.table.side_effect = Exception("Database connection error")
        
        result = check_owner_exists(TEST_OWNER_ID)
        
        # Should return the default value (False) due to handle_exceptions decorator
        assert result is False


def test_check_owner_exists_supabase_query_structure():
    """Test that check_owner_exists constructs the correct Supabase query."""
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = (None, [{"owner_id": TEST_OWNER_ID}])
        
        check_owner_exists(TEST_OWNER_ID)
        
        # Verify the query is constructed correctly
        mock_supabase.table.assert_called_once_with(table_name="owners")
        mock_table.select.assert_called_once_with("owner_id")
        mock_select.eq.assert_called_once_with(column="owner_id", value=TEST_OWNER_ID)
        mock_eq.execute.assert_called_once()


def test_check_owner_exists_boolean_conversion():
    """Test that check_owner_exists properly converts data to boolean."""
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        
        # Test with truthy data
        mock_eq.execute.return_value = (None, [{"owner_id": TEST_OWNER_ID}])
        result = check_owner_exists(TEST_OWNER_ID)
        assert result is True
        assert isinstance(result, bool)
        
        # Test with falsy data
        mock_eq.execute.return_value = (None, [])
        result = check_owner_exists(TEST_OWNER_ID)
        assert result is False
        assert isinstance(result, bool)
        
        # Test with None data
        mock_eq.execute.return_value = (None, None)
        result = check_owner_exists(TEST_OWNER_ID)
        assert result is False
        assert isinstance(result, bool)
