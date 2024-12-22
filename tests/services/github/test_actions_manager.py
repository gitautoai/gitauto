import pytest
from unittest.mock import Mock, patch
from services.github.actions_manager import ActionsManager

@pytest.fixture
def mock_github_api():
    return Mock()

@pytest.fixture
def actions_manager(mock_github_api):
    return ActionsManager(github_api=mock_github_api)

def test_example(actions_manager):
    # Example test case
    assert actions_manager is not None
