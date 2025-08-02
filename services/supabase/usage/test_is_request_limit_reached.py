    owner_id = 67890
    owner_name = "test-owner"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer:
        mock_get_customer.side_effect = Exception("Test exception")
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result == DEFAULT  # Should return default value due to exception handling
