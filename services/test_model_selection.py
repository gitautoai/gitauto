from unittest.mock import patch, MagicMock
import pytest

from config import (
    ANTHROPIC_MODEL_ID_35,
    ANTHROPIC_MODEL_ID_37,
    ANTHROPIC_MODEL_ID_40,
    OPENAI_MODEL_ID_O3_MINI,
)
from services.model_selection import (
    MODEL_CHAIN,
    get_model,
    try_next_model,
    _current_model,
)


@pytest.fixture
def reset_model_state():
    """Fixture to reset the global model state before each test."""
    # Import the module to access the global variable
    import services.model_selection as model_selection
    
    # Store original state
    original_model = model_selection._current_model
    
    # Reset to initial state
    model_selection._current_model = MODEL_CHAIN[0]
    
    yield
    
    # Restore original state
    model_selection._current_model = original_model


@pytest.fixture
def mock_colorize():
    """Fixture to mock the colorize function."""
    with patch("services.model_selection.colorize") as mock:
        mock.return_value = "mocked_colored_text"
        yield mock


@pytest.fixture
def mock_print():
    """Fixture to mock the print function."""
    with patch("builtins.print") as mock:
        yield mock


def test_model_chain_contains_expected_models():
    """Test that MODEL_CHAIN contains the expected models in correct order."""
    expected_models = [
        ANTHROPIC_MODEL_ID_40,
        ANTHROPIC_MODEL_ID_37,
        ANTHROPIC_MODEL_ID_35,
        OPENAI_MODEL_ID_O3_MINI,
    ]
    assert MODEL_CHAIN == expected_models
    assert len(MODEL_CHAIN) == 4


def test_model_chain_order():
    """Test that models are in the expected priority order."""
    assert MODEL_CHAIN[0] == ANTHROPIC_MODEL_ID_40  # Highest priority
    assert MODEL_CHAIN[1] == ANTHROPIC_MODEL_ID_37
    assert MODEL_CHAIN[2] == ANTHROPIC_MODEL_ID_35
    assert MODEL_CHAIN[3] == OPENAI_MODEL_ID_O3_MINI  # Lowest priority


def test_get_model_returns_current_model(reset_model_state):
    """Test that get_model returns the current model."""
    result = get_model()
    assert result == ANTHROPIC_MODEL_ID_40  # Initial model


def test_get_model_returns_string():
    """Test that get_model returns a string."""
    result = get_model()
    assert isinstance(result, str)
    assert len(result) > 0


def test_try_next_model_from_first_model(reset_model_state, mock_colorize, mock_print):
    """Test switching from first model to second model."""
    # Ensure we start with the first model
    assert get_model() == ANTHROPIC_MODEL_ID_40
    
    success, new_model = try_next_model()
    
    assert success is True
    assert new_model == ANTHROPIC_MODEL_ID_37
    assert get_model() == ANTHROPIC_MODEL_ID_37
    
    # Verify colorize was called with correct message and color
    expected_msg = f"Switching from {ANTHROPIC_MODEL_ID_40} to {ANTHROPIC_MODEL_ID_37}"
    mock_colorize.assert_called_once_with(expected_msg, "yellow")
    
    # Verify print was called with colorized message
    mock_print.assert_called_once_with("mocked_colored_text")


def test_try_next_model_from_second_model(reset_model_state, mock_colorize, mock_print):
    """Test switching from second model to third model."""
    import services.model_selection as model_selection
    
    # Set current model to second model
    model_selection._current_model = ANTHROPIC_MODEL_ID_37
    
    success, new_model = try_next_model()
    
    assert success is True
    assert new_model == ANTHROPIC_MODEL_ID_35
    assert get_model() == ANTHROPIC_MODEL_ID_35
    
    # Verify colorize was called with correct message
    expected_msg = f"Switching from {ANTHROPIC_MODEL_ID_37} to {ANTHROPIC_MODEL_ID_35}"
    mock_colorize.assert_called_once_with(expected_msg, "yellow")
    mock_print.assert_called_once_with("mocked_colored_text")


def test_try_next_model_from_third_model(reset_model_state, mock_colorize, mock_print):
    """Test switching from third model to fourth model."""
    import services.model_selection as model_selection
    
    # Set current model to third model
    model_selection._current_model = ANTHROPIC_MODEL_ID_35
    
    success, new_model = try_next_model()
    
    assert success is True
    assert new_model == OPENAI_MODEL_ID_O3_MINI
    assert get_model() == OPENAI_MODEL_ID_O3_MINI
    
    # Verify colorize was called with correct message
    expected_msg = f"Switching from {ANTHROPIC_MODEL_ID_35} to {OPENAI_MODEL_ID_O3_MINI}"
    mock_colorize.assert_called_once_with(expected_msg, "yellow")
    mock_print.assert_called_once_with("mocked_colored_text")


def test_try_next_model_from_last_model(reset_model_state, mock_colorize, mock_print):
    """Test that trying to switch from the last model returns False."""
    import services.model_selection as model_selection
    
    # Set current model to last model
    model_selection._current_model = OPENAI_MODEL_ID_O3_MINI
    
    success, current_model = try_next_model()
    
    assert success is False
    assert current_model == OPENAI_MODEL_ID_O3_MINI
    assert get_model() == OPENAI_MODEL_ID_O3_MINI
    
    # Verify no colorize or print calls were made
    mock_colorize.assert_not_called()
    mock_print.assert_not_called()


def test_try_next_model_sequential_calls(reset_model_state, mock_colorize, mock_print):
    """Test sequential calls to try_next_model through all models."""
    # Start with first model
    assert get_model() == ANTHROPIC_MODEL_ID_40
    
    # First call: switch to second model
    success1, model1 = try_next_model()
    assert success1 is True
    assert model1 == ANTHROPIC_MODEL_ID_37
    assert get_model() == ANTHROPIC_MODEL_ID_37
    
    # Second call: switch to third model
    success2, model2 = try_next_model()
    assert success2 is True
    assert model2 == ANTHROPIC_MODEL_ID_35
    assert get_model() == ANTHROPIC_MODEL_ID_35
    
    # Third call: switch to fourth model
    success3, model3 = try_next_model()
    assert success3 is True
    assert model3 == OPENAI_MODEL_ID_O3_MINI
    assert get_model() == OPENAI_MODEL_ID_O3_MINI
    
    # Fourth call: no more models available
    success4, model4 = try_next_model()
    assert success4 is False
    assert model4 == OPENAI_MODEL_ID_O3_MINI
    assert get_model() == OPENAI_MODEL_ID_O3_MINI
    
    # Verify colorize was called 3 times (for successful switches)
    assert mock_colorize.call_count == 3
    assert mock_print.call_count == 3


def test_try_next_model_return_types():
    """Test that try_next_model returns correct types."""
    success, model = try_next_model()
    
    assert isinstance(success, bool)
    assert isinstance(model, str)
    assert len(model) > 0


def test_model_selection_state_persistence(reset_model_state):
    """Test that model state persists between function calls."""
    # Initial state
    assert get_model() == ANTHROPIC_MODEL_ID_40
    
    # Switch model
    try_next_model()
    assert get_model() == ANTHROPIC_MODEL_ID_37
    
    # State should persist
    assert get_model() == ANTHROPIC_MODEL_ID_37
    
    # Switch again
    try_next_model()
    assert get_model() == ANTHROPIC_MODEL_ID_35
    
    # State should still persist
    assert get_model() == ANTHROPIC_MODEL_ID_35