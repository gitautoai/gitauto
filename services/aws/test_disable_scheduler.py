# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from services.aws.disable_scheduler import disable_scheduler


# Shape mirrors the real get_schedule response, including read-only metadata.
# Fields it should echo into update_schedule mirror ../website/app/actions/aws/create-or-update-schedule.ts.
GET_SCHEDULE_RESPONSE = {
    "Name": "gitauto-repo-123-456",
    "GroupName": "default",
    "ScheduleExpression": "cron(0 15 ? * MON-FRI *)",
    "Target": {
        "Arn": "arn:aws:lambda:us-west-1:123:function:pr-agent-prod",
        "RoleArn": "arn:aws:iam::123:role/scheduler",
        "Input": '{"ownerId":123,"repoId":456,"triggerType":"schedule"}',
    },
    "FlexibleTimeWindow": {"Mode": "OFF"},
    "State": "ENABLED",
    "Description": "GitAuto scheduled trigger for repository foo/bar",
    "ActionAfterCompletion": "NONE",
    # Read-only metadata that get_schedule returns but update_schedule rejects:
    "Arn": "arn:aws:scheduler:us-west-1:123:schedule/default/gitauto-repo-123-456",
    "CreationDate": "2026-01-01T00:00:00Z",
    "LastModificationDate": "2026-04-01T00:00:00Z",
    "ResponseMetadata": {"RequestId": "abc", "HTTPStatusCode": 200},
}


@pytest.fixture
def mock_scheduler_client():
    with patch("services.aws.disable_scheduler.scheduler_client") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    with patch("services.aws.disable_scheduler.logger") as mock:
        yield mock


def test_disable_scheduler_success(mock_scheduler_client, mock_logger):
    mock_scheduler_client.get_schedule.return_value = dict(GET_SCHEDULE_RESPONSE)
    mock_scheduler_client.update_schedule.return_value = {"ScheduleArn": "arn:..."}

    result = disable_scheduler("gitauto-repo-123-456")

    assert result is True
    mock_scheduler_client.get_schedule.assert_called_once_with(
        Name="gitauto-repo-123-456"
    )
    mock_scheduler_client.update_schedule.assert_called_once_with(
        Name="gitauto-repo-123-456",
        GroupName="default",
        ScheduleExpression="cron(0 15 ? * MON-FRI *)",
        Target=GET_SCHEDULE_RESPONSE["Target"],
        FlexibleTimeWindow={"Mode": "OFF"},
        State="DISABLED",
        Description="GitAuto scheduled trigger for repository foo/bar",
        ActionAfterCompletion="NONE",
    )
    mock_logger.info.assert_any_call(
        "Disabled EventBridge Scheduler: %s", "gitauto-repo-123-456"
    )


def test_disable_scheduler_forwards_timezone_not_in_hardcoded_set(
    mock_scheduler_client, mock_logger
):
    """Whitelist comes from UpdateScheduleInputTypeDef, so optional fields the website
    never sets (e.g. ScheduleExpressionTimezone) are still forwarded if present on
    the schedule. Read-only metadata stays out."""
    response = dict(GET_SCHEDULE_RESPONSE)
    response["ScheduleExpressionTimezone"] = "America/New_York"
    mock_scheduler_client.get_schedule.return_value = response

    disable_scheduler("gitauto-repo-123-456")

    kwargs = mock_scheduler_client.update_schedule.call_args.kwargs
    assert kwargs == {
        "Name": "gitauto-repo-123-456",
        "GroupName": "default",
        "ScheduleExpression": "cron(0 15 ? * MON-FRI *)",
        "Target": GET_SCHEDULE_RESPONSE["Target"],
        "FlexibleTimeWindow": {"Mode": "OFF"},
        "State": "DISABLED",
        "Description": "GitAuto scheduled trigger for repository foo/bar",
        "ActionAfterCompletion": "NONE",
        "ScheduleExpressionTimezone": "America/New_York",
    }


def test_disable_scheduler_not_found(mock_scheduler_client, mock_logger):
    mock_scheduler_client.get_schedule.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
        "GetSchedule",
    )

    result = disable_scheduler("missing-schedule")

    assert result is True
    mock_scheduler_client.update_schedule.assert_not_called()
    mock_logger.info.assert_called_once_with(
        "EventBridge Scheduler not found: %s", "missing-schedule"
    )


def test_disable_scheduler_access_denied(mock_scheduler_client, mock_logger):
    mock_scheduler_client.get_schedule.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "GetSchedule",
    )

    result = disable_scheduler("restricted-schedule")

    assert result is False
    mock_scheduler_client.update_schedule.assert_not_called()
