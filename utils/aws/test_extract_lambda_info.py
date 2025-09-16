from unittest.mock import Mock, PropertyMock

from fastapi import Request
from utils.aws.extract_lambda_info import extract_lambda_info


def test_extract_lambda_info_with_aws_context():
    """Test extracting Lambda info when AWS context is available"""
    # Create mock request with AWS scope
    request = Mock(spec=Request)
    mock_context = Mock()
    mock_context.log_group_name = "/aws/lambda/pr-agent-prod"
    mock_context.log_stream_name = "2025/09/04/pr-agent-prod[$LATEST]841315c5"
    mock_context.aws_request_id = "17921070-5cb6-43ee-8d2e-b5161ae89729"

    request.scope = {"aws.context": mock_context}

    result = extract_lambda_info(request)

    assert result == {
        "log_group": "/aws/lambda/pr-agent-prod",
        "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
        "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
    }


def test_extract_lambda_info_without_aws_scope():
    """Test extracting Lambda info when AWS scope is not available"""
    request = Mock(spec=Request)
    request.scope = {}

    result = extract_lambda_info(request)

    assert not result


def test_extract_lambda_info_with_aws_scope_no_context():
    """Test extracting Lambda info when AWS scope exists but no context"""
    request = Mock(spec=Request)
    request.scope = {"aws": {}}  # This should still return empty since "aws.context" key doesn't exist

    result = extract_lambda_info(request)

    assert not result


def test_extract_lambda_info_with_missing_attributes():
    """Test extracting Lambda info when context has missing attributes"""
    request = Mock(spec=Request)
    mock_context = Mock()
    # Set specific attributes and configure spec to avoid mock objects for missing attrs
    mock_context.log_group_name = "/aws/lambda/pr-agent-prod"
    # Configure side_effect to return None for missing attributes
    mock_context.configure_mock(**{"log_stream_name": None, "aws_request_id": None})

    request.scope = {"aws.context": mock_context}

    result = extract_lambda_info(request)

    assert result == {
        "log_group": "/aws/lambda/pr-agent-prod",
        "log_stream": None,
        "request_id": None,
    }


def test_extract_lambda_info_with_exception():
    """Test extracting Lambda info when an exception occurs"""
    request = Mock(spec=Request)
    # Make request.scope raise an exception when accessed
    type(request).scope = PropertyMock(side_effect=Exception("Request error"))

    # Should return empty dict due to handle_exceptions decorator
    result = extract_lambda_info(request)

    assert not result
