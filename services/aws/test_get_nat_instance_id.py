# pylint: disable=import-outside-toplevel,unused-argument
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_ec2_client():
    with patch("services.aws.get_nat_instance_id.ec2_client") as mock_client:
        yield mock_client


class TestGetNatInstanceId:
    def test_returns_instance_id_when_found(self, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"InstanceId": "i-1234567890abcdef0"}]}]
        }

        from services.aws.get_nat_instance_id import get_nat_instance_id

        result = get_nat_instance_id()
        assert result == "i-1234567890abcdef0"

        mock_ec2_client.describe_instances.assert_called_once_with(
            Filters=[
                {"Name": "tag:Name", "Values": ["gitauto-nat-instance"]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ]
        )

    def test_returns_none_when_no_reservations(self, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {"Reservations": []}

        from services.aws.get_nat_instance_id import get_nat_instance_id

        result = get_nat_instance_id()
        assert result is None

    def test_returns_none_when_no_instances(self, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": []}]
        }

        from services.aws.get_nat_instance_id import get_nat_instance_id

        result = get_nat_instance_id()
        assert result is None
