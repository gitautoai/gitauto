# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os

from services.env.set_env import set_env


def test_set_env_creates_new_var(create_test_base_args):
    key = "TEST_SET_ENV_NEW"
    os.environ.pop(key, None)
    base_args = create_test_base_args()
    result = set_env(key=key, value="hello", base_args=base_args)
    assert os.environ[key] == "hello"
    assert "TEST_SET_ENV_NEW" in result
    os.environ.pop(key, None)


def test_set_env_overwrites_existing_var(create_test_base_args):
    key = "TEST_SET_ENV_OVERWRITE"
    os.environ[key] = "old"
    base_args = create_test_base_args()
    set_env(key=key, value="new", base_args=base_args)
    assert os.environ[key] == "new"
    os.environ.pop(key, None)
