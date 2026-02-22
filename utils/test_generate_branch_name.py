# pylint: disable=import-outside-toplevel
import re
from unittest.mock import patch


def test_setup_trigger():
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

                result = generate_branch_name(trigger="setup")
                assert result == "gitauto/setup-20241224-120000-XYZ1"


def test_schedule_trigger():
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

                result = generate_branch_name(trigger="schedule")
                assert result == "gitauto/schedule-20241224-120000-ABCD"


def test_branch_name_format_schedule():
    from config import PRODUCT_ID
    from utils.generate_branch_name import generate_branch_name

    result = generate_branch_name(trigger="schedule")
    pattern = rf"^{re.escape(PRODUCT_ID)}/schedule-\d{{8}}-\d{{6}}-[a-zA-Z0-9]{{4}}$"
    assert re.match(
        pattern, result
    ), f"Branch name '{result}' doesn't match expected pattern"


def test_branch_name_format_dashboard():
    from config import PRODUCT_ID
    from utils.generate_branch_name import generate_branch_name

    result = generate_branch_name(trigger="dashboard")
    pattern = rf"^{re.escape(PRODUCT_ID)}/dashboard-\d{{8}}-\d{{6}}-[a-zA-Z0-9]{{4}}$"
    assert re.match(
        pattern, result
    ), f"Branch name '{result}' doesn't match expected pattern"
