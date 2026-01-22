# pylint: disable=global-statement
# pylint: disable=invalid-name

from config import OPENAI_MODEL_ID_GPT_5
from constants.claude import (
    CLAUDE_MODEL_ID_37,
    CLAUDE_MODEL_ID_40,
    CLAUDE_MODEL_ID_45,
)
from utils.logging.logging_config import logger

MODEL_CHAIN = [
    CLAUDE_MODEL_ID_45,
    CLAUDE_MODEL_ID_40,
    CLAUDE_MODEL_ID_37,
    OPENAI_MODEL_ID_GPT_5,
]

_current_model = MODEL_CHAIN[0]


def get_model():
    return _current_model


def try_next_model():
    global _current_model
    current_index = MODEL_CHAIN.index(_current_model)
    if current_index + 1 < len(MODEL_CHAIN):
        next_model = MODEL_CHAIN[current_index + 1]
        logger.warning("Switching from %s to %s", _current_model, next_model)
        _current_model = next_model
        return True, _current_model
    return False, _current_model
