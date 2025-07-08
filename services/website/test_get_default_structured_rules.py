# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.website.get_default_structured_rules import get_default_structured_rules


@pytest.fixture
def mock_requests_get():
    """Fixture to provide a mocked requests.get."""
    with patch("services.website.get_default_structured_rules.requests.get") as mock:
        yield mock


@pytest.fixture
def sample_structured_rules():
    """Fixture providing sample structured rules data."""
    return {
        "codePatternStrategy": "Best practices first",
        "preferredApiApproach": "GraphQL first",
        "customTestConstantsPath": "",
        "preferredCommentLanguage": "Auto-detect",
        "enforceOneFunctionPerFile": True,
        "customTestFileNamingPattern": "",
        "preferConciseCodeTechniques": True,
        "fixUnrelatedIssuesWhenNoticed": False,
        "allowCreatingIntermediateLayers": False,
        "customIntegrationTestFileSuffix": "",
        "enforceOneResponsibilityPerFile": True,
        "includeJSDocOrDocstringComments": False,
        "placeTestFilesNextToSourceFiles": True,
        "separateUnitAndIntegrationTests": True,
        "testConstantsManagementStrategy": "Auto-detect from existing tests",
        "allowTodoCommentsInGeneratedCode": False,
        "enforceComponentIsolationInTests": True,
        "enableCommentsInGeneratedTestCode": False,
        "preferEarlyReturnsToReduceNesting": True,
        "preferredTestFileNamingConvention": "filename_test.ext (Go style)",
        "preferredIntegrationTestFileSuffix": "Auto-detect language conventions",
        "preferredTestConstantsFileLocation": "Auto-detect from project structure",
        "enableCommentsInGeneratedSourceCode": False,
        "preferFunctionStyleOverClassStyleInTests": True,
        "enableIntegrationTestsForReadOnlyOperations": False,
        "allowRefactoringSourceCodeBeforeWritingTests": True,
        "enableComprehensiveTestCoverageIncludingEdgeCases": True,
        "enableMockingExternalDependenciesInComponentTests": True,
        "preferFunctionComponentsOverClassComponentsInTests": True
    }


def test_get_default_structured_rules_success(mock_requests_get, sample_structured_rules):
    """Test successful retrieval of default structured rules."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = sample_structured_rules
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = get_default_structured_rules()
    
    # Verify API call
    mock_requests_get.assert_called_once_with(
        url="https://gitauto.ai/api/structured-rules-default",
        timeout=120
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    # Verify result
    assert result == sample_structured_rules
    assert isinstance(result, dict)
    assert "codePatternStrategy" in result
    assert "preferredApiApproach" in result


def test_get_default_structured_rules_empty_response(mock_requests_get):
    """Test handling of empty response."""
    # Setup mock response with empty data
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = get_default_structured_rules()
    
    # Verify API call
    mock_requests_get.assert_called_once_with(
        url="https://gitauto.ai/api/structured-rules-default",
        timeout=120
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    # Verify result
    assert result == {}
    assert isinstance(result, dict)


def test_get_default_structured_rules_http_error_404(mock_requests_get):
    """Test handling of 404 HTTP error."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "API endpoint not found"
    
    http_error = requests.exceptions.HTTPError("404 Client Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    mock_requests_get.return_value = mock_response
    
    # Call function - should return {} due to handle_exceptions decorator
    result = get_default_structured_rules()
    
    # Verify result is {} (default_return_value from decorator)
    assert result == {}
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_default_structured_rules_http_error_500(mock_requests_get):
    """Test handling of 500 HTTP error."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Internal server error"
    
    http_error = requests.exceptions.HTTPError("500 Server Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    mock_requests_get.return_value = mock_response
    
    # Call function - should return {} due to handle_exceptions decorator
    result = get_default_structured_rules()
    
    # Verify result is {} (default_return_value from decorator)
    assert result == {}
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_default_structured_rules_network_error(mock_requests_get):
    """Test handling of network connection error."""
    # Setup mock to raise connection error
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")
    
    # Call function - should return {} due to handle_exceptions decorator
    result = get_default_structured_rules()
    
    # Verify result is {} (default_return_value from decorator)
    assert result == {}
    mock_requests_get.assert_called_once()


def test_get_default_structured_rules_timeout_error(mock_requests_get):
    """Test handling of timeout error."""
    # Setup mock to raise timeout error
    mock_requests_get.side_effect = requests.exceptions.Timeout("Request timeout")
    
    # Call function - should return {} due to handle_exceptions decorator
    result = get_default_structured_rules()
    
    # Verify result is {} (default_return_value from decorator)
    assert result == {}
    mock_requests_get.assert_called_once()


def test_get_default_structured_rules_json_decode_error(mock_requests_get):
    """Test handling of JSON decode error."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response
    
    # Call function - should return {} due to handle_exceptions decorator
    result = get_default_structured_rules()
    
    # Verify result is {} (default_return_value from decorator)
    assert result == {}
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_default_structured_rules_url_construction():
    """Test that the URL is constructed correctly."""
    with patch("services.website.get_default_structured_rules.requests.get") as mock_get, \
         patch("services.website.get_default_structured_rules.BASE_URL", "https://custom-domain.com"):
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        # Call function
        get_default_structured_rules()
        
        # Verify URL construction
        mock_get.assert_called_once_with(
            url="https://custom-domain.com/api/structured-rules-default",
            timeout=120
        )


def test_get_default_structured_rules_timeout_parameter():
    """Test that the timeout parameter is correctly used."""
    with patch("services.website.get_default_structured_rules.requests.get") as mock_get, \
         patch("services.website.get_default_structured_rules.TIMEOUT", 60):
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        # Call function
        get_default_structured_rules()
        
        # Verify timeout parameter
        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 60


def test_get_default_structured_rules_partial_data(mock_requests_get):
    """Test handling of partial structured rules data."""
    # Setup mock response with partial data
    partial_data = {
        "codePatternStrategy": "Best practices first",
        "preferredApiApproach": "GraphQL first"
    }
    mock_response = MagicMock()
    mock_response.json.return_value = partial_data
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = get_default_structured_rules()
    
    # Verify result
    assert result == partial_data
    assert len(result) == 2
    assert "codePatternStrategy" in result
    assert "preferredApiApproach" in result
