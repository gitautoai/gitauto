# pyright: reportUnusedVariable=false
from unittest.mock import patch

from utils.system.get_runtime_description import get_runtime_description


def test_production_lambda_al2023():
    # Real production case: Lambda invocation on Amazon Linux 2023.
    fake_env = {"AWS_LAMBDA_FUNCTION_NAME": "pr-agent-prod"}
    with patch.dict("os.environ", fake_env, clear=True), patch(
        "utils.system.get_runtime_description.read_os_release_pretty_name",
        return_value="Amazon Linux 2023",
    ):
        assert get_runtime_description() == "AWS Lambda, Amazon Linux 2023"


def test_function_name_value_is_not_leaked_into_output():
    # The function name "totally-internal-function-name" is set in the env but must not appear in the rendered tag — exact-match output proves it.
    fake_env = {"AWS_LAMBDA_FUNCTION_NAME": "totally-internal-function-name"}
    with patch.dict("os.environ", fake_env, clear=True), patch(
        "utils.system.get_runtime_description.read_os_release_pretty_name",
        return_value="Amazon Linux 2023",
    ):
        assert get_runtime_description() == "AWS Lambda, Amazon Linux 2023"


def test_does_not_keep_saying_amazon_linux_2023_when_runtime_upgrades():
    # Regression: if a future runtime upgrade lands without code changes, the function must reflect the new PRETTY_NAME — that was the exact hardcoding the function was created to eliminate.
    fake_env = {"AWS_LAMBDA_FUNCTION_NAME": "pr-agent-prod"}
    with patch.dict("os.environ", fake_env, clear=True), patch(
        "utils.system.get_runtime_description.read_os_release_pretty_name",
        return_value="Amazon Linux 2024",
    ):
        assert get_runtime_description() == "AWS Lambda, Amazon Linux 2024"
