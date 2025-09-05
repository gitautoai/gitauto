from config import UTF8
from utils.logs.deduplicate_logs import deduplicate_logs


def test_deduplicate_logs_with_real_sample():
    with open(
        "services/github/workflow_runs/get_workflow_run_logs_duplicated.txt",
        "r",
        encoding=UTF8,
    ) as f:
        original_log = f.read()

    with open(
        "services/github/workflow_runs/get_workflow_run_logs_deduplicated.txt",
        "r",
        encoding=UTF8,
    ) as f:
        expected_content = f.read()

    deduplicated = deduplicate_logs(original_log)

    original_lines = original_log.split("\n")
    deduplicated_lines = deduplicated.split("\n")
    expected_lines = expected_content.split("\n")

    # Check exact line count matches expected
    assert (
        len(original_lines) == 14581
    ), f"Expected 14581 original lines, got {len(original_lines)}"
    assert (
        len(deduplicated_lines) == 254
    ), f"Expected 254 deduplicated lines, got {len(deduplicated_lines)}"
    assert (
        len(expected_lines) == 280
    ), f"Expected file should have 280 lines, got {len(expected_lines)}"


def test_sentry_issue_agent_146_real_error_log():
    """
    Test deduplication with the actual Sentry issue AGENT-146 error log that caused 167,154 token context limit error.
    This massive log (194K chars) contains:
    - 72+ scattered MaxListenersExceededWarning messages
    - Massive insurance JSON form data
    - Real MongoDB/AWS errors buried in the noise

    The deduplication should dramatically reduce size while preserving actual errors.
    """
    # Load the real Sentry issue AGENT-146 error log from AWS CloudWatch
    with open(
        "payloads/aws/cloudwatch/agent_146_error_log.txt", "r", encoding=UTF8
    ) as f:
        agent_146_log = f.read()

    deduplicated = deduplicate_logs(agent_146_log)

    # Count occurrences in the real massive log
    original_max_listeners = agent_146_log.count("MaxListenersExceededWarning")
    deduplicated_max_listeners = deduplicated.count("MaxListenersExceededWarning")

    original_business_info = agent_146_log.count("BusinessInformation_")
    deduplicated_business_info = deduplicated.count("BusinessInformation_")

    original_coverage = agent_146_log.count("Coverage_Munich_")
    deduplicated_coverage = deduplicated.count("Coverage_Munich_")

    # Verify exact deduplication results
    assert (
        original_max_listeners == 72
    ), f"Expected exactly 72 MaxListenersExceededWarning in real log, got {original_max_listeners}"
    assert (
        deduplicated_max_listeners == 2
    ), f"Expected exactly 2 MaxListenersExceededWarning after dedup, got {deduplicated_max_listeners}"

    # Insurance data counts (these don't get deduplicated as they're below 3 threshold)
    assert (
        original_business_info == 28
    ), f"Expected exactly 28 BusinessInformation_ entries, got {original_business_info}"
    assert (
        deduplicated_business_info == 28
    ), f"Expected exactly 28 BusinessInformation_ entries after dedup (below threshold), got {deduplicated_business_info}"
    assert (
        original_coverage == 16
    ), f"Expected exactly 16 Coverage_ entries, got {original_coverage}"
    assert (
        deduplicated_coverage == 16
    ), f"Expected exactly 16 Coverage_ entries after dedup (below threshold), got {deduplicated_coverage}"

    # Verify actual error info is preserved
    assert "AccessDeniedException" in deduplicated, "Real AWS error should be preserved"
    assert "MongoDBConnection" in deduplicated, "MongoDB errors should be preserved"
    assert "yarn test" in deduplicated, "Test command should be preserved"

    # Check exact size reduction on real data
    original_length = len(agent_146_log)
    deduplicated_length = len(deduplicated)
    reduction_percent = (1 - deduplicated_length / original_length) * 100

    # Exact size assertions for predictable behavior (updated for ANSI removal)
    assert (
        original_length == 194117
    ), f"Expected exactly 194117 chars in original log, got {original_length:,}"
    assert (
        deduplicated_length == 60557
    ), f"Expected exactly 60557 chars after ANSI+deduplication, got {deduplicated_length:,}"
    assert (
        abs(reduction_percent - 68.8) < 0.1
    ), f"Expected exactly 68.8% reduction, got {reduction_percent:.1f}%"

    print("Sentry issue AGENT-146 real error log deduplication:")
    print(f"  Original: {original_length:,} characters")
    print(f"  Deduplicated: {deduplicated_length:,} characters")
    print(f"  Reduction: {reduction_percent:.1f}%")
    print(
        f"  MaxListenersExceededWarning: {original_max_listeners} -> {deduplicated_max_listeners}"
    )
    print(
        f"  BusinessInformation_: {original_business_info} -> {deduplicated_business_info}"
    )
    print(f"  Coverage_Munich_: {original_coverage} -> {deduplicated_coverage}")

    # This reduction would have prevented the 167,154 token context limit error
    assert (
        deduplicated_length == 60557
    ), f"Deduplicated log should be exactly 60557 chars, got {deduplicated_length:,}"


def test_sentry_issue_agent_146_insurance_json_patterns():
    """
    Test that insurance JSON patterns from Sentry issue AGENT-146 are properly handled
    """
    # Insurance form JSON that appeared in Sentry issue AGENT-146
    insurance_json_log = """
"BusinessInformation_100_9219DroneUsage_WORLD_EN":{"inSortedList":true,"questionLabel":"Do you use drones?","questionType":"customboolean","value":"No"},
"BusinessInformation_100_9219IndependentContractors_WORLD_EN":{"inSortedList":true,"questionLabel":"Independent contractors?","questionType":"customboolean","value":"No"},
"BusinessInformation_100_9219DroneUsage_WORLD_EN":{"inSortedList":true,"questionLabel":"Do you use drones?","questionType":"customboolean","value":"No"},
"Coverage_Munich_201_9219_CGLAggregateLimit_WORLD_EN":{"inSortedList":true,"questionLabel":"CGL Limit","questionType":"custominput","value":"2000000"},
"BusinessInformation_100_9219DroneUsage_WORLD_EN":{"inSortedList":true,"questionLabel":"Do you use drones?","questionType":"customboolean","value":"No"},
Actual error message here
"Coverage_Munich_201_9219_CGLAggregateLimit_WORLD_EN":{"inSortedList":true,"questionLabel":"CGL Limit","questionType":"custominput","value":"2000000"},
"""

    deduplicated = deduplicate_logs(insurance_json_log)

    # Count drone usage entries (appeared 3 times)
    original_drone = insurance_json_log.count(
        "BusinessInformation_100_9219DroneUsage_WORLD_EN"
    )
    deduplicated_drone = deduplicated.count(
        "BusinessInformation_100_9219DroneUsage_WORLD_EN"
    )

    # Count coverage entries (appeared 2 times - should be kept)
    original_coverage = insurance_json_log.count(
        "Coverage_Munich_201_9219_CGLAggregateLimit_WORLD_EN"
    )
    deduplicated_coverage = deduplicated.count(
        "Coverage_Munich_201_9219_CGLAggregateLimit_WORLD_EN"
    )

    assert original_drone == 3, f"Expected 3 drone entries, got {original_drone}"
    assert (
        deduplicated_drone == 1
    ), f"Expected 1 drone entry after dedup, got {deduplicated_drone}"

    assert (
        original_coverage == 2
    ), f"Expected 2 coverage entries, got {original_coverage}"
    assert (
        deduplicated_coverage == 2
    ), f"Expected 2 coverage entries after dedup (below 3+ threshold), got {deduplicated_coverage}"

    # Verify actual error is preserved
    assert "Actual error message here" in deduplicated, "Real error should be preserved"


def test_ansi_escape_sequence_removal():
    """
    Test that ANSI escape sequences are properly removed
    """
    log_with_ansi = """
Some regular log message
\x1b[0mReset formatting\x1b[0m
\x1b[90mDark gray text\x1b[90m
\x1b[39mDefault color\x1b[39m
Another normal message
"""

    deduplicated = deduplicate_logs(log_with_ansi)

    # ANSI sequences should be completely removed
    assert "\x1b[0m" not in deduplicated, "Reset formatting codes should be removed"
    assert "\x1b[90m" not in deduplicated, "Dark gray codes should be removed"
    assert "\x1b[39m" not in deduplicated, "Default color codes should be removed"

    # Regular content should be preserved
    assert (
        "Some regular log message" in deduplicated
    ), "Regular content should be preserved"
    assert "Reset formatting" in deduplicated, "Text content should be preserved"
    assert "Dark gray text" in deduplicated, "Text content should be preserved"
    assert "Default color" in deduplicated, "Text content should be preserved"
    assert (
        "Another normal message" in deduplicated
    ), "Regular content should be preserved"


if __name__ == "__main__":
    test_sentry_issue_agent_146_real_error_log()
    test_sentry_issue_agent_146_insurance_json_patterns()
    test_ansi_escape_sequence_removal()
    print("All deduplication tests passed!")
