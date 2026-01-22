# pylint: disable=protected-access
import sys

import pytest

from config import OPENAI_MODEL_ID_GPT_5
from constants.claude import (
    CLAUDE_MODEL_ID_37,
    CLAUDE_MODEL_ID_40,
    CLAUDE_MODEL_ID_45,
)
from services import model_selection
from services.model_selection import MODEL_CHAIN, get_model, try_next_model


@pytest.fixture
def _():
    """Fixture to reset the global model state before each test."""
    # Store original state
    original_model = model_selection._current_model

    # Reset to initial state
    model_selection._current_model = MODEL_CHAIN[0]

    yield

    # Restore original state
    model_selection._current_model = original_model


def test_model_chain_contains_expected_models():
    """Test that MODEL_CHAIN contains the expected models in correct order."""
    expected_models = [
        CLAUDE_MODEL_ID_45,
        CLAUDE_MODEL_ID_40,
        CLAUDE_MODEL_ID_37,
        OPENAI_MODEL_ID_GPT_5,
    ]
    assert MODEL_CHAIN == expected_models
    assert len(MODEL_CHAIN) == 4


def test_model_chain_order():
    """Test that models are in the expected priority order."""
    assert MODEL_CHAIN[0] == CLAUDE_MODEL_ID_45  # Highest priority
    assert MODEL_CHAIN[1] == CLAUDE_MODEL_ID_40
    assert MODEL_CHAIN[2] == CLAUDE_MODEL_ID_37
    assert MODEL_CHAIN[3] == OPENAI_MODEL_ID_GPT_5  # Lowest priority


def test_get_model_returns_current_model(_):
    """Test that get_model returns the current model."""
    result = get_model()
    assert result == CLAUDE_MODEL_ID_45  # Initial model


def test_get_model_returns_string():
    """Test that get_model returns a string."""
    result = get_model()
    assert isinstance(result, str)
    assert len(result) > 0


def test_try_next_model_from_first_model(_, caplog):
    """Test switching from first model to second model."""
    # Ensure we start with the first model
    assert get_model() == CLAUDE_MODEL_ID_45

    success, new_model = try_next_model()

    assert success is True
    assert new_model == CLAUDE_MODEL_ID_40
    assert get_model() == CLAUDE_MODEL_ID_40

    # Verify log message was emitted
    assert f"Switching from {CLAUDE_MODEL_ID_45} to {CLAUDE_MODEL_ID_40}" in caplog.text


def test_try_next_model_from_second_model(_, caplog):
    """Test switching from second model to third model."""
    # Set current model to second model
    model_selection._current_model = CLAUDE_MODEL_ID_40

    success, new_model = try_next_model()

    assert success is True
    assert new_model == CLAUDE_MODEL_ID_37
    assert get_model() == CLAUDE_MODEL_ID_37

    # Verify log message was emitted
    assert f"Switching from {CLAUDE_MODEL_ID_40} to {CLAUDE_MODEL_ID_37}" in caplog.text


def test_try_next_model_from_third_model(_, caplog):
    """Test switching from third model to fourth model."""
    # Set current model to third model
    model_selection._current_model = CLAUDE_MODEL_ID_37

    success, new_model = try_next_model()

    assert success is True
    assert new_model == OPENAI_MODEL_ID_GPT_5
    assert get_model() == OPENAI_MODEL_ID_GPT_5

    # Verify log message was emitted
    assert (
        f"Switching from {CLAUDE_MODEL_ID_37} to {OPENAI_MODEL_ID_GPT_5}" in caplog.text
    )


def test_try_next_model_from_last_model(_, caplog):
    """Test that trying to switch from the last model returns False."""
    # Set current model to last model
    model_selection._current_model = OPENAI_MODEL_ID_GPT_5

    success, current_model = try_next_model()

    assert success is False
    assert current_model == OPENAI_MODEL_ID_GPT_5
    assert get_model() == OPENAI_MODEL_ID_GPT_5

    # Verify no log message was emitted
    assert "Switching from" not in caplog.text


def test_try_next_model_sequential_calls(_, caplog):
    """Test sequential calls to try_next_model through all models."""
    # Start with first model
    assert get_model() == CLAUDE_MODEL_ID_45

    # First call: switch to second model
    success1, model1 = try_next_model()
    assert success1 is True
    assert model1 == CLAUDE_MODEL_ID_40
    assert get_model() == CLAUDE_MODEL_ID_40

    # Second call: switch to third model
    success2, model2 = try_next_model()
    assert success2 is True
    assert model2 == CLAUDE_MODEL_ID_37
    assert get_model() == CLAUDE_MODEL_ID_37

    # Third call: switch to fourth model
    success3, model3 = try_next_model()
    assert success3 is True
    assert model3 == OPENAI_MODEL_ID_GPT_5
    assert get_model() == OPENAI_MODEL_ID_GPT_5

    # Fourth call: no more models available
    success4, model4 = try_next_model()
    assert success4 is False
    assert model4 == OPENAI_MODEL_ID_GPT_5
    assert get_model() == OPENAI_MODEL_ID_GPT_5

    # Verify log was emitted 3 times (for successful switches)
    assert caplog.text.count("Switching from") == 3


def test_try_next_model_return_types():
    """Test that try_next_model returns correct types."""
    success, model = try_next_model()

    assert isinstance(success, bool)
    assert isinstance(model, str)
    assert len(model) > 0


def test_model_selection_state_persistence(_):
    """Test that model state persists between function calls."""
    # Initial state
    assert get_model() == CLAUDE_MODEL_ID_45

    # Switch model
    try_next_model()
    assert get_model() == CLAUDE_MODEL_ID_40

    # State should persist
    assert get_model() == CLAUDE_MODEL_ID_40

    # Switch again
    try_next_model()
    assert get_model() == CLAUDE_MODEL_ID_37

    # State should still persist
    assert get_model() == CLAUDE_MODEL_ID_37


def test_try_next_model_with_invalid_current_model(_):
    """Test behavior when _current_model is not in MODEL_CHAIN."""
    # Set an invalid current model
    model_selection._current_model = "invalid-model"

    # This should raise a ValueError when trying to find the index
    with pytest.raises(ValueError):
        try_next_model()


def test_get_model_consistency():
    """Test that get_model always returns the same value until model is switched."""
    model1 = get_model()
    model2 = get_model()
    model3 = get_model()

    assert model1 == model2 == model3


def test_logging_on_model_switch(_, caplog):
    """Test that logging is called with correct parameters on switch."""
    try_next_model()

    # Verify log message contains expected content
    assert "Switching from" in caplog.text
    assert "to" in caplog.text


def test_module_level_constants():
    """Test that module-level constants are properly defined."""
    # Test that MODEL_CHAIN is a list
    assert isinstance(MODEL_CHAIN, list)

    # Test that all models in chain are strings
    for model in MODEL_CHAIN:
        assert isinstance(model, str)
        assert len(model) > 0

    # Test that there are no duplicate models
    assert len(MODEL_CHAIN) == len(set(MODEL_CHAIN))


@pytest.mark.parametrize("model_index", [0, 1, 2, 3])
def test_try_next_model_from_each_position(_, model_index):
    """Test try_next_model behavior when starting from each model position."""
    # Set current model to the specified index
    model_selection._current_model = MODEL_CHAIN[model_index]

    success, new_model = try_next_model()

    if model_index < len(MODEL_CHAIN) - 1:
        # Should successfully switch to next model
        assert success is True
        assert new_model == MODEL_CHAIN[model_index + 1]
        assert get_model() == MODEL_CHAIN[model_index + 1]
    else:
        # Should fail to switch (already at last model)
        assert success is False
        assert new_model == MODEL_CHAIN[model_index]
        assert get_model() == MODEL_CHAIN[model_index]


def test_global_state_isolation():
    """Test that global state changes don't affect other imports."""
    # Import the module again to test isolation
    if "services.model_selection" in sys.modules:
        original_model = model_selection.get_model()

        # Change the model
        model_selection.try_next_model()
        new_model = model_selection.get_model()

        # Verify the change persisted in the same module reference
        assert new_model != original_model

        # Verify get_model() returns the same value
        assert get_model() == new_model
