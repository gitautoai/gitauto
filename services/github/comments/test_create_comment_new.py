    assert result is None  # The handle_exceptions decorator should return None on error
    assert "headers" in mock_post.call_args[1]
    assert mock_post.call_args[1]["json"] == {"body": "Test comment"}
