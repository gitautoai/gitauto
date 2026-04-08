"""Manually trigger the schedule handler for a specific repo.

EventBridge schedules fire automatically, but sometimes we need to re-trigger
manually (e.g. after deploying a fix, or when a scheduled run failed).

Uses async Lambda invocation (InvocationType=Event) to avoid the CLI's 60s read
timeout causing retries - the schedule handler typically takes 2+ minutes, and
synchronous invocation retries created duplicate Lambda runs.

Usage:
    python3 scripts/aws/trigger_schedule.py Foxquilt foxden-admin-portal
"""

import json
import sys

import boto3

REGION = "us-west-1"
LAMBDA_FUNCTION = "pr-agent-prod"


def find_schedule_payload(owner: str, repo: str):
    client = boto3.client("scheduler", region_name=REGION)
    paginator = client.get_paginator("list_schedules")
    for page in paginator.paginate(GroupName="default"):
        for schedule in page["Schedules"]:
            state = schedule.get("State")
            if state != "ENABLED":
                continue
            name = schedule.get("Name")
            if not name:
                continue
            detail = client.get_schedule(Name=name)
            payload_str = detail["Target"].get("Input")
            if not payload_str:
                continue
            payload = json.loads(payload_str)
            if payload.get("ownerName") == owner and payload.get("repoName") == repo:
                return payload
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/aws/trigger_schedule.py <owner> <repo>")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    payload = find_schedule_payload(owner, repo)
    if not payload:
        print(f"No enabled schedule found for {owner}/{repo}")
        sys.exit(1)

    print(f"Found schedule for {owner}/{repo}")
    print(json.dumps(payload, indent=2))

    # Async invocation: fire-and-forget, no CLI timeout retries
    client = boto3.client("lambda", region_name=REGION)
    response = client.invoke(
        FunctionName=LAMBDA_FUNCTION,
        InvocationType="Event",
        Payload=json.dumps(payload),
    )
    print(f"Invoked (async): StatusCode={response['StatusCode']}")


if __name__ == "__main__":
    main()
