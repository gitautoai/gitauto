import os
import base64
import pytest
from datetime import datetime, timezone
from config import (
    get_env_var,
    GITHUB_APP_IDS,
    GITHUB_CHECK_RUN_FAILURES,
    GITHUB_ISSUE_TEMPLATES,
    OPENAI_FINAL_STATUSES,
    DEFAULT_TIME,
    TZ,
    IS_PRD,
)

def test_get_env_var_success():
    os.environ["TEST_VAR"] = "test_value"
    assert get_env_var("TEST_VAR") == "test_value"

def test_get_env_var_missing():
    if "NON_EXISTENT_VAR" in os.environ:
        del os.environ["NON_EXISTENT_VAR"]
    with pytest.raises(ValueError) as exc_info:
        get_env_var("NON_EXISTENT_VAR")
    assert str(exc_info.value) == "Environment variable NON_EXISTENT_VAR not set."

def test_get_env_var_empty_string():
    os.environ["EMPTY_VAR"] = ""
    assert get_env_var("EMPTY_VAR") == ""

def test_github_app_ids_unique():
    assert len(GITHUB_APP_IDS) == len(set(GITHUB_APP_IDS))
    assert isinstance(GITHUB_APP_IDS, list)
    assert all(isinstance(id, int) for id in GITHUB_APP_IDS)

def test_github_check_run_failures():
    expected_failures = [
        "startup_failure",
        "failure",
        "timed_out",
        "action_required",
    ]
    assert GITHUB_CHECK_RUN_FAILURES == expected_failures
    assert all(isinstance(status, str) for status in GITHUB_CHECK_RUN_FAILURES)

def test_github_issue_templates():
    expected_templates = ["bug_report.yml", "feature_request.yml"]
    assert GITHUB_ISSUE_TEMPLATES == expected_templates
    assert all(template.endswith(".yml") for template in GITHUB_ISSUE_TEMPLATES)

def test_openai_final_statuses():
    expected_statuses = ["cancelled", "completed", "expired", "failed"]
    assert OPENAI_FINAL_STATUSES == expected_statuses
    assert all(isinstance(status, str) for status in OPENAI_FINAL_STATUSES)

def test_default_time():
    assert isinstance(DEFAULT_TIME, datetime)
    assert DEFAULT_TIME == datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)

def test_timezone():
    assert TZ == timezone.utc

def test_environment_dependent_settings():
    os.environ["ENV"] = "production"
    from config import IS_PRD as is_prd_prod
    assert is_prd_prod is True

    os.environ["ENV"] = "dev"
    import importlib
    import config
    importlib.reload(config)
    assert config.IS_PRD is False

def test_github_private_key_encoding():
    test_key = "test_private_key"
    encoded_key = base64.b64encode(test_key.encode()).decode()
    os.environ["GH_PRIVATE_KEY"] = encoded_key
    
    import importlib
    import config
    importlib.reload(config)
    
    assert config.GITHUB_PRIVATE_KEY_ENCODED == encoded_key
    assert config.GITHUB_PRIVATE_KEY == test_key.encode()

def test_openai_max_values_positive():
    from config import OPENAI_MAX_ARRAY_LENGTH, OPENAI_MAX_STRING_LENGTH, OPENAI_MAX_CONTEXT_TOKENS
    
    assert OPENAI_MAX_ARRAY_LENGTH > 0
    assert OPENAI_MAX_STRING_LENGTH > 0
    assert OPENAI_MAX_CONTEXT_TOKENS > 0
