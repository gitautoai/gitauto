import argparse
import json
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def get_sentry_issue(issue_id: str):
    sentry_token = os.getenv("SENTRY_PERSONAL_TOKEN")
    sentry_org = os.getenv("SENTRY_ORG_SLUG")

    if not sentry_token or not sentry_org:
        print("Error: SENTRY_PERSONAL_TOKEN and SENTRY_ORG_SLUG must be set in .env")
        sys.exit(1)

    url = f"https://sentry.io/api/0/organizations/{sentry_org}/issues/{issue_id}/events/latest/"
    headers = {
        "Authorization": f"Bearer {sentry_token}",
    }

    print(f"Fetching Sentry issue {issue_id}...")
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON response: {e}")
        sys.exit(1)

    output_path = f"/tmp/sentry_{issue_id.lower()}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\nIssue ID: {issue_id}")
    print(f"Event ID: {data.get('eventID')}")
    print(f"Timestamp: {data.get('dateCreated')}")
    print(f"Full JSON saved to: {output_path}")
    print()

    for entry in data.get("entries", []):  # pylint: disable=too-many-nested-blocks
        if entry.get("type") == "message":
            formatted_message = entry.get("data", {}).get("formatted", "")
            print("=" * 80)
            print("ERROR MESSAGE:")
            print("=" * 80)
            print(formatted_message[:2000])
            if len(formatted_message) > 2000:
                print(
                    f"\n... (truncated, total length: {len(formatted_message)} chars)"
                )
            print()

        elif entry.get("type") == "exception":
            print("=" * 80)
            print("EXCEPTION:")
            print("=" * 80)
            for value in entry.get("data", {}).get("values", []):
                print(f"Type: {value.get('type')}")
                print(f"Value: {value.get('value')}")
                print(f"Module: {value.get('module')}")
                print()

                stacktrace = value.get("stacktrace", {})
                frames = stacktrace.get("frames", [])
                if frames:
                    print(f"Stack trace ({len(frames)} frames):")
                    print()

                    for frame in frames[-10:]:
                        print(f"  File: {frame.get('filename')}:{frame.get('lineno')}")
                        print(f"  Function: {frame.get('function')}")
                        if frame.get("context_line"):
                            print(f"  Line: {frame.get('context_line').strip()}")
                        print()

    contexts = data.get("contexts", {})
    if "cloudwatch logs" in contexts:
        print("=" * 80)
        print("CLOUDWATCH LOGS:")
        print("=" * 80)
        cw_info = contexts["cloudwatch logs"]
        if "url" in cw_info:
            print(f"URL: {cw_info['url']}")
        if "log_stream" in cw_info:
            print(f"Stream: {cw_info['log_stream']}")
        print()

    if "trace" in contexts:
        trace = contexts["trace"]
        if "aws_request_id" in trace:
            print(f"AWS Request ID: {trace['aws_request_id']}")
        print()

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Sentry issue details")
    parser.add_argument("issue_id", help="Sentry issue ID (e.g., AGENT-20N)")

    args = parser.parse_args()
    get_sentry_issue(args.issue_id)
