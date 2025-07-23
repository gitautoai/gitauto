from utils.text.comment_identifiers import (
    TEST_SELECTION_COMMENT_IDENTIFIER,
    PROGRESS_BAR_FILLED,
    PROGRESS_BAR_EMPTY,
)


def test_test_selection_comment_identifier():
    assert TEST_SELECTION_COMMENT_IDENTIFIER == "## 🧪 Manage Tests?"
    assert isinstance(TEST_SELECTION_COMMENT_IDENTIFIER, str)


def test_progress_bar_filled():
    assert PROGRESS_BAR_FILLED == "▓"
    assert isinstance(PROGRESS_BAR_FILLED, str)


def test_progress_bar_empty():
    assert PROGRESS_BAR_EMPTY == "░"
    assert isinstance(PROGRESS_BAR_EMPTY, str)
