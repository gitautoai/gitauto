# run this file locally with: python -m tests.test_github_manager

import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import time
import jwt
import requests
from fastapi import Request
from typing import Any
from config import (
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GITHUB_APP_ID,
    GITHUB_APP_IDS,
    GITHUB_PRIVATE_KEY,
    PRODUCT_NAME,
    PRODUCT_URL,
    TIMEOUT_IN_SECONDS,
    PRODUCT_ID,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    UTF8,
)
from services.github.github_types import (
    GitHubContentInfo,
    GitHubLabeledPayload,
    IssueInfo,
)
from services.supabase import SupabaseManager
from utils.file_manager import apply_patch, extract_file_name, run_command
from utils.handle_exceptions import handle_exceptions
from utils.text_copy import (
    UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY,
    UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE,
    request_issue_comment,
    request_limit_reached,
)
from services.github.github_manager import GitHubManager

def test_add_label_to_issue():
    gh_manager = GitHubManager()
    assert gh_manager.add_label_to_issue(owner="test_owner", repo="test_repo", issue_number=1, label="bug", token="test_token") is None

def test_commit_multiple_changes_to_remote_branch():
    gh_manager = GitHubManager()
    assert gh_manager.commit_multiple_changes_to_remote_branch(diffs=["diff --git a/file.txt b/file.txt"], new_branch="test_branch", owner="test_owner", repo="test_repo", token="test_token") is None
# run this file locally with: python -m tests.test_github_manager
