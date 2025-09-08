#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.getcwd())

from unittest.mock import patch
from services.github.trees.get_file_tree_list import get_file_tree_list

# Mock data
mock_tree_items = [
    {"path": "README.md", "type": "blob"},
    {"path": "main.py", "type": "blob"},
    {"path": "config.py", "type": "blob"},
    {"path": ".github", "type": "tree"},
    {"path": ".github/workflows", "type": "tree"},
    {"path": ".github/workflows/ci.yml", "type": "blob"},
    {"path": "services", "type": "tree"},
    {"path": "services/github", "type": "tree"},
    {"path": "services/openai", "type": "tree"},
    {"path": "utils", "type": "tree"},
]

base_args = {
    "owner": "test",
    "repo": "test",
    "base_branch": "main",
    "token": "test",
}

def test_slash_only():
    with patch("services.github.trees.get_file_tree_list.get_file_tree") as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items
        result = get_file_tree_list(base_args, dir_path="/")
        expected = [".github/", "services/", "utils/", "README.md", "config.py", "main.py"]
        print(f"Slash only test: {result == expected}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")

def test_whitespace():
    with patch("services.github.trees.get_file_tree_list.get_file_tree") as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items
        result = get_file_tree_list(base_args, dir_path="  services  ")
        expected = ["github/", "openai/"]
        print(f"Whitespace test: {result == expected}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")

if __name__ == "__main__":
    test_slash_only()
    test_whitespace()
