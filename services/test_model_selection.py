# pylint: disable=protected-access
import sys

import pytest

from constants.claude import ClaudeModelId
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
        ClaudeModelId.OPUS_4_6,
        ClaudeModelId.SONNET_4_6,
        ClaudeModelId.SONNET_4_5,
        ClaudeModelId.SONNET_4_0,
    ]
    assert MODEL_CHAIN == expected_models
    assert len(MODEL_CHAIN) == 4


def test_model_chain_order():
    """Test that models are in the expected priority order."""
    assert MODEL_CHAIN[0] == ClaudeModelId.OPUS_4_6  # Highest priority
    assert MODEL_CHAIN[1] == ClaudeModelId.SONNET_4_6
    assert MODEL_CHAIN[2] == ClaudeModelId.SONNET_4_5
    assert MODEL_CHAIN[3] == ClaudeModelId.SONNET_4_0  # Lowest priority


def test_get_model_returns_current_model(_):
    """Test that get_model returns the current model."""
    result = get_model()
    assert result == ClaudeModelId.OPUS_4_6  # Initial model


def test_get_model_returns_string():
    """Test that get_model returns a string."""
    result = get_model()
    assert isinstance(result, str)
    assert len(result) > 0


def test_try_next_model_from_first_model(_, caplog):
    """Test switching from first model to second model."""
    assert get_model() == ClaudeModelId.OPUS_4_6

    success, new_model = try_next_model()

    assert success is True
    assert new_model == ClaudeModelId.SONNET_4_6
    assert get_model() == ClaudeModelId.SONNET_4_6

    assert (
        f"Switching from {ClaudeModelId.OPUS_4_6} to {ClaudeModelId.SONNET_4_6}"
        in caplog.text
    )


def test_try_next_model_from_second_model(_, caplog):
    """Test switching from second model to third model."""
    model_selection._current_model = ClaudeModelId.SONNET_4_6

    success, new_model = try_next_model()

    assert success is True
    assert new_model == ClaudeModelId.SONNET_4_5
    assert get_model() == ClaudeModelId.SONNET_4_5

    assert (
        f"Switching from {ClaudeModelId.SONNET_4_6} to {ClaudeModelId.SONNET_4_5}"
        in caplog.text
    )


def test_try_next_model_from_last_model(_, caplog):
    """Test that trying to switch from the last model returns False."""
    model_selection._current_model = ClaudeModelId.SONNET_4_0

    success, current_model = try_next_model()

    assert success is False
    assert current_model == ClaudeModelId.SONNET_4_0
    assert get_model() == ClaudeModelId.SONNET_4_0

    assert "Switching from" not in caplog.text


def test_try_next_model_sequential_calls(_, caplog):
    """Test sequential calls to try_next_model through all models."""
    assert get_model() == ClaudeModelId.OPUS_4_6

    success1, model1 = try_next_model()
    assert success1 is True
    assert model1 == ClaudeModelId.SONNET_4_6
    assert get_model() == ClaudeModelId.SONNET_4_6

    success2, model2 = try_next_model()
    assert success2 is True
    assert model2 == ClaudeModelId.SONNET_4_5
    assert get_model() == ClaudeModelId.SONNET_4_5

    success3, model3 = try_next_model()
    assert success3 is True
    assert model3 == ClaudeModelId.SONNET_4_0
    assert get_model() == ClaudeModelId.SONNET_4_0

    success4, model4 = try_next_model()
    assert success4 is False
    assert model4 == ClaudeModelId.SONNET_4_0
    assert get_model() == ClaudeModelId.SONNET_4_0

    assert caplog.text.count("Switching from") == 3


def test_try_next_model_return_types():
    """Test that try_next_model returns correct types."""
    success, model = try_next_model()

    assert isinstance(success, bool)
    assert isinstance(model, str)
    assert len(model) > 0


def test_model_selection_state_persistence(_):
    """Test that model state persists between function calls."""
    assert get_model() == ClaudeModelId.OPUS_4_6

    try_next_model()
    assert get_model() == ClaudeModelId.SONNET_4_6
    assert get_model() == ClaudeModelId.SONNET_4_6

    try_next_model()
    assert get_model() == ClaudeModelId.SONNET_4_5
    assert get_model() == ClaudeModelId.SONNET_4_5


def test_try_next_model_with_invalid_current_model(_):
    """Test behavior when _current_model is not in MODEL_CHAIN."""
    model_selection._current_model = "invalid-model"

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

    assert "Switching from" in caplog.text
    assert "to" in caplog.text


def test_module_level_constants():
    """Test that module-level constants are properly defined."""
    assert isinstance(MODEL_CHAIN, list)

    for model in MODEL_CHAIN:
        assert isinstance(model, str)
        assert len(model) > 0

    assert len(MODEL_CHAIN) == len(set(MODEL_CHAIN))


@pytest.mark.parametrize("model_index", [0, 1, 2, 3])
def test_try_next_model_from_each_position(_, model_index):
    """Test try_next_model behavior when starting from each model position."""
    model_selection._current_model = MODEL_CHAIN[model_index]

    success, new_model = try_next_model()

    if model_index < len(MODEL_CHAIN) - 1:
        assert success is True
        assert new_model == MODEL_CHAIN[model_index + 1]
        assert get_model() == MODEL_CHAIN[model_index + 1]
    else:
        assert success is False
        assert new_model == MODEL_CHAIN[model_index]
        assert get_model() == MODEL_CHAIN[model_index]


def test_global_state_isolation():
    """Test that global state changes don't affect other imports."""
    if "services.model_selection" in sys.modules:
        original_model = model_selection.get_model()

        model_selection.try_next_model()
        new_model = model_selection.get_model()

        assert new_model != original_model
        assert get_model() == new_model
