from utils.text.comment_identifiers import (
    PROGRESS_BAR_FILLED,
    PROGRESS_BAR_EMPTY,
)


def test_progress_bar_filled():
    assert PROGRESS_BAR_FILLED == "▓"
    assert isinstance(PROGRESS_BAR_FILLED, str)


def test_progress_bar_empty():
    assert PROGRESS_BAR_EMPTY == "░"
    assert isinstance(PROGRESS_BAR_EMPTY, str)
