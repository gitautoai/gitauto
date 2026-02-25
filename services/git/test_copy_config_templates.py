# pylint: disable=redefined-outer-name
import os

import pytest

from config import UTF8
from services.git.copy_config_templates import copy_config_templates


@pytest.fixture
def clone_dir(tmp_path):
    return str(tmp_path)


def test_copies_default_file(clone_dir):
    template = os.path.join(clone_dir, "conf", "preference.inc.default")
    target = os.path.join(clone_dir, "conf", "preference.inc")
    os.makedirs(os.path.dirname(template))
    with open(template, "w", encoding=UTF8) as f:
        f.write("config content")

    copy_config_templates(clone_dir)

    assert os.path.exists(target)
    with open(target, encoding=UTF8) as f:
        assert f.read() == "config content"


def test_copies_example_file(clone_dir):
    template = os.path.join(clone_dir, ".env.example")
    target = os.path.join(clone_dir, ".env")
    with open(template, "w", encoding=UTF8) as f:
        f.write("SECRET=abc")

    copy_config_templates(clone_dir)

    assert os.path.exists(target)


def test_copies_sample_file(clone_dir):
    template = os.path.join(clone_dir, "config.sample")
    target = os.path.join(clone_dir, "config")
    with open(template, "w", encoding=UTF8) as f:
        f.write("sample")

    copy_config_templates(clone_dir)

    assert os.path.exists(target)


def test_skips_when_target_exists(clone_dir):
    template = os.path.join(clone_dir, ".env.example")
    target = os.path.join(clone_dir, ".env")
    with open(template, "w", encoding=UTF8) as f:
        f.write("new content")
    with open(target, "w", encoding=UTF8) as f:
        f.write("existing content")

    copy_config_templates(clone_dir)

    with open(target, encoding=UTF8) as f:
        assert f.read() == "existing content"


def test_skips_vendor_directory(clone_dir):
    vendor_template = os.path.join(clone_dir, "vendor", "pkg", "config.default")
    vendor_target = os.path.join(clone_dir, "vendor", "pkg", "config")
    os.makedirs(os.path.dirname(vendor_template))
    with open(vendor_template, "w", encoding=UTF8) as f:
        f.write("vendor config")

    copy_config_templates(clone_dir)

    assert not os.path.exists(vendor_target)


def test_skips_node_modules_directory(clone_dir):
    nm_template = os.path.join(clone_dir, "node_modules", "pkg", ".env.example")
    nm_target = os.path.join(clone_dir, "node_modules", "pkg", ".env")
    os.makedirs(os.path.dirname(nm_template))
    with open(nm_template, "w", encoding=UTF8) as f:
        f.write("nm config")

    copy_config_templates(clone_dir)

    assert not os.path.exists(nm_target)


def test_no_templates_found(clone_dir):
    with open(os.path.join(clone_dir, "README.md"), "w", encoding=UTF8) as f:
        f.write("hello")

    copy_config_templates(clone_dir)
