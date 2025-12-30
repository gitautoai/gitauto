import os
import pytest
from utils.env import get_env_var


def test_get_env_var_success():
    test_var_name = "TEST_ENV_VAR"
    test_value = "test_value"
    os.environ[test_var_name] = test_value
    assert get_env_var(test_var_name) == test_value
    del os.environ[test_var_name]


def test_get_env_var_not_set():
    test_var_name = "NONEXISTENT_ENV_VAR"
    if test_var_name in os.environ:
        del os.environ[test_var_name]

    with pytest.raises(ValueError) as exc_info:
        get_env_var(test_var_name)
    assert str(exc_info.value) == f"Environment variable {test_var_name} not set."
