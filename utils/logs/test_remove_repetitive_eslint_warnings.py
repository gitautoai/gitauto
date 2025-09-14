#!/usr/bin/env python3

import os

from remove_repetitive_eslint_warnings import remove_repetitive_eslint_warnings

from config import UTF8


def test_remove_repetitive_eslint_warnings():
    payload_path = os.path.join(
        os.path.dirname(__file__), "../../payloads/circleci/eslint_build_log.txt"
    )

    with open(payload_path, "r", encoding=UTF8) as f:
        test_log = f.read()

    cleaned_path = os.path.join(
        os.path.dirname(__file__),
        "../../payloads/circleci/eslint_build_log_cleaned.txt",
    )
    with open(cleaned_path, "r", encoding=UTF8) as f:
        expected_output = f.read()  # Expected output with collapsed repetitive warnings

    result = remove_repetitive_eslint_warnings(test_log)

    assert result == expected_output, f"Expected:\n{expected_output}\n\nGot:\n{result}"

    print("✅ Test passed!")


if __name__ == "__main__":
    test_remove_repetitive_eslint_warnings()
