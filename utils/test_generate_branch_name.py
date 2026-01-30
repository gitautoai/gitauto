# pylint: disable=import-outside-toplevel
import re
from unittest.mock import patch


def test_with_issue_number():
    with patch("utils.generate_branch_name.PRODUCT_ID", "gitauto"):
        with patch("utils.generate_branch_name.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.side_effect = [
                "20241224",
                "120000",
            ]
            with patch(
                "utils.generate_branch_name.choices",
                return_value=["A", "B", "C", "D"],
            ):
                from utils.generate_branch_name import generate_branch_name

                result = generate_branch_name(issue_number=123)
                assert result == "gitauto/issue-123-20241224-120000-ABCD"


def test_without_issue_number():
    with patch("utils.generate_branch_name.PRODUCT_ID", "gitauto"):
        with patch("utils.generate_branch_name.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.side_effect = [
                "20241224",
                "120000",
            ]
            with patch(
                "utils.generate_branch_name.choices",
                return_value=["X", "Y", "Z", "1"],
            ):
                from utils.generate_branch_name import generate_branch_name

                result = generate_branch_name()
                assert result == "gitauto/setup-20241224-120000-XYZ1"


def test_branch_name_format_with_issue():
    from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
    from utils.generate_branch_name import generate_branch_name

    result = generate_branch_name(issue_number=456)
    pattern = rf"^{re.escape(PRODUCT_ID)}{re.escape(ISSUE_NUMBER_FORMAT)}456-\d{{8}}-\d{{6}}-[a-zA-Z0-9]{{4}}$"
    assert re.match(
        pattern, result
    ), f"Branch name '{result}' doesn't match expected pattern"


def test_branch_name_format_without_issue():
    from config import PRODUCT_ID
    from utils.generate_branch_name import generate_branch_name

    result = generate_branch_name()
    pattern = rf"^{re.escape(PRODUCT_ID)}/setup-\d{{8}}-\d{{6}}-[a-zA-Z0-9]{{4}}$"
    assert re.match(
        pattern, result
    ), f"Branch name '{result}' doesn't match expected pattern"
