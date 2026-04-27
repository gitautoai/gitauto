from unittest.mock import MagicMock, patch

from utils.env.get_internal_env_var_names import (
    SSM_GITAUTO_PREFIX,
    get_internal_env_var_names,
)


def _clear_cache():
    get_internal_env_var_names.cache_clear()


@patch("utils.env.get_internal_env_var_names.IS_PRD", False)
def test_returns_empty_set_locally():
    """Local dev has no customer subprocess to leak to, no AWS IAM, and no boto3 cold-start cost — the scrub set is empty by design."""
    _clear_cache()
    assert get_internal_env_var_names() == set()


@patch("utils.env.get_internal_env_var_names.ssm_client")
@patch("utils.env.get_internal_env_var_names.IS_PRD", True)
def test_strips_prefix_from_ssm_names(mock_ssm):
    """SSM stores names like /gitauto/SENTRY_DSN; we strip /gitauto/ to match the env var name on the Lambda."""
    _clear_cache()
    paginator = MagicMock()
    # Real-shape DescribeParameters response: a list of dicts, each with "Name". Other fields exist on the API but we only read "Name".
    paginator.paginate.return_value = [
        {
            "Parameters": [
                {"Name": "/gitauto/SENTRY_DSN"},
                {"Name": "/gitauto/OPENAI_API_KEY"},
                {"Name": "/gitauto/GH_PRIVATE_KEY"},
            ]
        },
        {
            "Parameters": [
                {"Name": "/gitauto/STRIPE_API_KEY"},
                {"Name": "/gitauto/SUPABASE_SERVICE_ROLE_KEY"},
            ]
        },
    ]
    mock_ssm.get_paginator.return_value = paginator

    result = get_internal_env_var_names()

    assert result == {
        "SENTRY_DSN",
        "OPENAI_API_KEY",
        "GH_PRIVATE_KEY",
        "STRIPE_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    }
    # Pagination is invoked with a BeginsWith filter on /gitauto/ — the boundary is the SSM path prefix, not Lambda env keys (which would also include operational vars like GIT_CONFIG_GLOBAL that subprocess needs).
    paginator.paginate.assert_called_once_with(
        ParameterFilters=[
            {
                "Key": "Name",
                "Option": "BeginsWith",
                "Values": [SSM_GITAUTO_PREFIX],
            }
        ]
    )


@patch("utils.env.get_internal_env_var_names.ssm_client")
@patch("utils.env.get_internal_env_var_names.IS_PRD", True)
def test_skips_params_missing_name(mock_ssm):
    """Defensive: if a page comes back with a Parameter dict that has no Name (shouldn't happen per the boto3 type, but the field is technically NotRequired), skip it instead of raising."""
    _clear_cache()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "Parameters": [
                {"Name": "/gitauto/SENTRY_DSN"},
                {},  # malformed
                {"Name": ""},  # falsy
            ]
        }
    ]
    mock_ssm.get_paginator.return_value = paginator

    assert get_internal_env_var_names() == {"SENTRY_DSN"}


@patch("utils.env.get_internal_env_var_names.ssm_client")
@patch("utils.env.get_internal_env_var_names.IS_PRD", True)
def test_returns_empty_set_on_ssm_failure(mock_ssm):
    """If SSM is unreachable, @handle_exceptions returns the default (set()) — meaning no scrubbing happens, but the function doesn't crash. The accompanying Sentry alert is the signal to investigate."""
    _clear_cache()
    mock_ssm.get_paginator.side_effect = RuntimeError("SSM throttled")

    assert get_internal_env_var_names() == set()


@patch("utils.env.get_internal_env_var_names.ssm_client")
@patch("utils.env.get_internal_env_var_names.IS_PRD", True)
def test_result_is_cached(mock_ssm):
    """SSM is queried at most once per process — the @cache decorator prevents per-subprocess-invocation cost."""
    _clear_cache()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {"Parameters": [{"Name": "/gitauto/SENTRY_DSN"}]}
    ]
    mock_ssm.get_paginator.return_value = paginator

    get_internal_env_var_names()
    get_internal_env_var_names()
    get_internal_env_var_names()

    assert mock_ssm.get_paginator.call_count == 1
