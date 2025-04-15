from .progress_bar import create_progress_bar


def test_create_progress_bar_normal():
    result = create_progress_bar(50, "Processing...")
    expected_filled = "▓" * 25
    expected_unfilled = "░" * 25
    assert result == f"{expected_filled}{expected_unfilled} 50%\nProcessing..."


def test_create_progress_bar_cap_at_95():
    result = create_progress_bar(100, "Almost done")
    expected_filled = "▓" * int(50 * 0.95)
    expected_unfilled = "░" * (50 - int(50 * 0.95))
    assert result == f"{expected_filled}{expected_unfilled} 95%\nAlmost done"


def test_create_progress_bar_zero():
    result = create_progress_bar(0, "Starting")
    expected_unfilled = "░" * 50
    assert result == f"{expected_unfilled} 0%\nStarting"


def test_create_progress_bar_exact_95():
    result = create_progress_bar(95, "Maximum progress")
    expected_filled = "▓" * int(50 * 0.95)
    expected_unfilled = "░" * (50 - int(50 * 0.95))
    assert result == f"{expected_filled}{expected_unfilled} 95%\nMaximum progress"


def test_create_progress_bar_empty_message():
    result = create_progress_bar(30, "")
    expected_filled = "▓" * 15
    expected_unfilled = "░" * 35
    assert result == f"{expected_filled}{expected_unfilled} 30%\n"


def test_create_progress_bar_long_message():
    long_msg = "This is a very long message that spans multiple words and should still work correctly with the progress bar"
    result = create_progress_bar(70, long_msg)
    expected_filled = "▓" * 35
    expected_unfilled = "░" * 15
    assert result == f"{expected_filled}{expected_unfilled} 70%\n{long_msg}"