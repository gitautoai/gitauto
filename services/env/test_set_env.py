# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
from typing import cast

from services.env.set_env import set_env
from services.types.base_args import BaseArgs

BASE_ARGS = cast(BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"})


def test_set_env_creates_new_var():
    key = "TEST_SET_ENV_NEW"
    os.environ.pop(key, None)
    result = set_env(key=key, value="hello", base_args=BASE_ARGS)
    assert os.environ[key] == "hello"
    assert "TEST_SET_ENV_NEW" in result
    os.environ.pop(key, None)


def test_set_env_overwrites_existing_var():
    key = "TEST_SET_ENV_OVERWRITE"
    os.environ[key] = "old"
    set_env(key=key, value="new", base_args=BASE_ARGS)
    assert os.environ[key] == "new"
    os.environ.pop(key, None)
