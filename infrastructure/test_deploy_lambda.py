"""Validate SSM parameter types match CloudFormation template expectations.

CloudFormation's {{resolve:ssm:...}} only works with String parameters.
SecureString parameters cause deployment failures with:
  'Non-secure ssm prefix was used for secure parameter'
"""

import re
from pathlib import Path

import boto3
import pytest

INFRA_DIR = Path(__file__).parent
CFN_TEMPLATE = INFRA_DIR / "deploy-lambda.yml"
SSM_RESOLVE_PATTERN = re.compile(r"\{\{resolve:ssm:(/[^}]+)\}\}")
AWS_REGION = "us-west-1"


def _get_ssm_param_names_from_template():
    """Extract all SSM parameter names referenced in the CloudFormation template."""
    content = CFN_TEMPLATE.read_text()
    return sorted(set(SSM_RESOLVE_PATTERN.findall(content)))


@pytest.mark.integration
def test_ssm_params_are_not_secure_string():
    """Every {{resolve:ssm:...}} parameter must be String, not SecureString."""
    param_names = _get_ssm_param_names_from_template()
    assert param_names, f"No SSM parameters found in {CFN_TEMPLATE}"

    ssm = boto3.client("ssm", region_name=AWS_REGION)
    # DescribeParameters accepts max 10 filters, but we can paginate by name
    secure_params: list[str] = []
    for name in param_names:
        response = ssm.describe_parameters(
            ParameterFilters=[{"Key": "Name", "Values": [name]}]
        )
        params = response.get("Parameters", [])
        if not params:
            pytest.fail(f"SSM parameter {name} not found in {AWS_REGION}")
        # Type is NotRequired in ParameterMetadataTypeDef; treat absence as a non-SecureString param (the assertion at the end only flags actual SecureStrings).
        if params[0].get("Type") == "SecureString":
            secure_params.append(name)

    assert not secure_params, (
        f"SecureString params can't be resolved by {{{{resolve:ssm:...}}}}. "
        f"Re-create as String: {secure_params}"
    )
