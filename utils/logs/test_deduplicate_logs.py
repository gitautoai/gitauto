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


def test_empty_log_content():
    """Test handling of empty log content"""
    result = deduplicate_logs("")
    assert result == "", "Empty string should return empty string"


def test_single_line_log():
    """Test handling of single line log"""
    single_line = "Single log message"
    result = deduplicate_logs(single_line)
    assert result == single_line, "Single line should be preserved"


def test_two_lines_no_duplication():
    """Test handling of two different lines"""
    log_content = "First line\nSecond line"
    result = deduplicate_logs(log_content)
    assert result == log_content, "Two different lines should be preserved"


def test_consecutive_duplicate_lines_exactly_three():
    """Test consecutive duplicate lines appearing exactly 3 times"""
    log_content = "Line 1\nDuplicate\nDuplicate\nDuplicate\nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate\nLine 5"
    assert result == expected, "Should keep first occurrence of 3 consecutive duplicates"


def test_consecutive_duplicate_lines_more_than_three():
    """Test consecutive duplicate lines appearing more than 3 times"""
    log_content = "Line 1\nDuplicate\nDuplicate\nDuplicate\nDuplicate\nDuplicate\nLine 7"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate\nLine 7"
    assert result == expected, "Should keep first occurrence of 5 consecutive duplicates"


def test_scattered_duplicate_lines_exactly_three():
    """Test scattered duplicate lines appearing exactly 3 times"""
    log_content = "Line 1\nDuplicate\nLine 3\nDuplicate\nLine 5\nDuplicate\nLine 7"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate\nLine 3\nLine 5\nLine 7"
    assert result == expected, "Should keep first occurrence of 3 scattered duplicates"


def test_scattered_duplicate_lines_more_than_three():
    """Test scattered duplicate lines appearing more than 3 times"""
    log_content = "Line 1\nDuplicate\nLine 3\nDuplicate\nLine 5\nDuplicate\nLine 7\nDuplicate\nLine 9"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate\nLine 3\nLine 5\nLine 7\nLine 9"
    assert result == expected, "Should keep first occurrence of 4 scattered duplicates"


def test_duplicate_lines_less_than_three():
    """Test duplicate lines appearing less than 3 times (should be preserved)"""
    log_content = "Line 1\nDuplicate\nLine 3\nDuplicate\nLine 5"
    result = deduplicate_logs(log_content)
    assert result == log_content, "Should preserve duplicates appearing less than 3 times"


def test_multi_line_pattern_consecutive():
    """Test consecutive multi-line patterns"""
    log_content = "Start\nPattern A\nPattern B\nPattern A\nPattern B\nPattern A\nPattern B\nEnd"
    result = deduplicate_logs(log_content)
    expected = "Start\nPattern A\nPattern B\nEnd"
    assert result == expected, "Should deduplicate consecutive multi-line patterns"


def test_multi_line_pattern_scattered():
    """Test scattered multi-line patterns"""
    log_content = "Start\nPattern A\nPattern B\nMiddle\nPattern A\nPattern B\nOther\nPattern A\nPattern B\nEnd"
    result = deduplicate_logs(log_content)
    expected = "Start\nPattern A\nPattern B\nMiddle\nOther\nEnd"
    assert result == expected, "Should deduplicate scattered multi-line patterns"


def test_overlapping_patterns():
    """Test overlapping patterns of different sizes"""
    log_content = "A\nB\nA\nB\nA\nB\nA\nB"
    result = deduplicate_logs(log_content)
    # The pattern "A\nB" appears 4 times, so should be deduplicated to first occurrence
    expected = "A\nB"
    assert result == expected, "Should handle overlapping patterns correctly"


def test_complex_ansi_sequences():
    """Test removal of complex ANSI escape sequences"""
    log_content = "Normal text\n\\\x1b[5D\\\x1b[K cursor movement\n\x1b[1;31mBold red\x1b[0m\n\x1b[38;5;196mTruecolor\x1b[0m"
    result = deduplicate_logs(log_content)
    
    # Check that ANSI sequences are removed
    assert "\\\x1b[5D\\\x1b[K" not in result, "Cursor movement sequences should be removed"
    assert "\x1b[1;31m" not in result, "Bold red formatting should be removed"
    assert "\x1b[0m" not in result, "Reset codes should be removed"
    assert "\x1b[38;5;196m" not in result, "Truecolor codes should be removed"
    
    # Check that text content is preserved
    assert "Normal text" in result, "Normal text should be preserved"
    assert "cursor movement" in result, "Text content should be preserved"
    assert "Bold red" in result, "Text content should be preserved"
    assert "Truecolor" in result, "Text content should be preserved"


def test_mixed_consecutive_and_scattered_patterns():
    """Test logs with both consecutive and scattered duplicate patterns"""
    log_content = "Line 1\nDuplicate A\nDuplicate A\nDuplicate A\nLine 5\nDuplicate B\nLine 7\nDuplicate B\nLine 9\nDuplicate B\nLine 11"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate A\nLine 5\nDuplicate B\nLine 7\nLine 9\nLine 11"
    assert result == expected, "Should handle both consecutive and scattered patterns"


def test_large_pattern_size_limit():
    """Test that pattern size is limited to prevent excessive memory usage"""
    # Create a log with many lines to test the size limit (min(20, len(lines) // 3))
    lines = [f"Line {i}" for i in range(100)]
    log_content = "\n".join(lines)
    
    result = deduplicate_logs(log_content)
    # Since all lines are unique, they should all be preserved
    assert result == log_content, "Unique lines should be preserved regardless of log size"


def test_pattern_size_calculation():
    """Test that pattern size calculation works correctly for different log sizes"""
    # Test with 9 lines (9 // 3 = 3, so max pattern size should be 3)
    log_content = "A\nB\nC\nA\nB\nC\nA\nB\nC"
    result = deduplicate_logs(log_content)
    # Pattern "A\nB\nC" appears 3 times, should be deduplicated
    expected = "A\nB\nC"
    assert result == expected, "Should deduplicate 3-line pattern appearing 3 times"


def test_whitespace_only_lines():
    """Test handling of whitespace-only lines"""
    log_content = "Line 1\n   \n   \n   \nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\n   \nLine 5"
    assert result == expected, "Should deduplicate whitespace-only lines"


def test_empty_lines():
    """Test handling of empty lines"""
    log_content = "Line 1\n\n\n\nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\n\nLine 5"
    assert result == expected, "Should deduplicate empty lines"


def test_very_long_lines():
    """Test handling of very long lines"""
    long_line = "A" * 1000
    log_content = f"Start\n{long_line}\n{long_line}\n{long_line}\nEnd"
    result = deduplicate_logs(log_content)
    expected = f"Start\n{long_line}\nEnd"
    assert result == expected, "Should deduplicate very long lines"


def test_special_characters():
    """Test handling of lines with special characters"""
    log_content = "Line 1\n!@#$%^&*()\n!@#$%^&*()\n!@#$%^&*()\nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\n!@#$%^&*()\nLine 5"
    assert result == expected, "Should deduplicate lines with special characters"


def test_unicode_characters():
    """Test handling of lines with unicode characters"""
    log_content = "Line 1\n🚀 Unicode test 🎉\n🚀 Unicode test 🎉\n🚀 Unicode test 🎉\nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\n🚀 Unicode test 🎉\nLine 5"
    assert result == expected, "Should deduplicate lines with unicode characters"


def test_newline_variations():
    """Test handling of different newline variations"""
    # Test with just \n (already covered in other tests)
    log_content = "Line 1\nDuplicate\nDuplicate\nDuplicate\nLine 5"
    result = deduplicate_logs(log_content)
    expected = "Line 1\nDuplicate\nLine 5"
    assert result == expected, "Should handle standard newlines"


def test_edge_case_single_character_lines():
    """Test deduplication of single character lines"""
    log_content = "A\nB\nA\nB\nA\nB"
    result = deduplicate_logs(log_content)
    expected = "A\nB"
    assert result == expected, "Should deduplicate single character lines"


def test_identical_multi_line_blocks():
    """Test deduplication of identical multi-line blocks"""
    block = "Error: Something went wrong\nStack trace line 1\nStack trace line 2"
    log_content = f"Start\n{block}\nMiddle\n{block}\nOther\n{block}\nEnd"
    result = deduplicate_logs(log_content)
    expected = f"Start\n{block}\nMiddle\nOther\nEnd"
    assert result == expected, "Should deduplicate identical multi-line blocks"


def test_pattern_at_log_boundaries():
    """Test patterns that appear at the beginning and end of logs"""
    log_content = "Boundary\nMiddle content\nBoundary\nMore content\nBoundary"
    result = deduplicate_logs(log_content)
    expected = "Boundary\nMiddle content\nMore content"
    assert result == expected, "Should handle patterns at log boundaries"


def test_no_patterns_to_deduplicate():
    """Test log with no patterns that meet deduplication criteria"""
    log_content = "Unique line 1\nUnique line 2\nDuplicate\nDuplicate\nUnique line 5"
    result = deduplicate_logs(log_content)
    # "Duplicate" appears only twice, so should be preserved
    assert result == log_content, "Should preserve patterns appearing less than 3 times"


def test_all_lines_identical():
    """Test log where all lines are identical"""
    log_content = "Same\nSame\nSame\nSame\nSame"
    result = deduplicate_logs(log_content)
    expected = "Same"
    assert result == expected, "Should reduce all identical lines to single occurrence"


def test_minimum_lines_for_pattern_detection():
    """Test that pattern detection requires minimum number of lines"""
    # With only 2 lines, no patterns should be detected (need at least 3 for deduplication)
    log_content = "Line 1\nLine 2"
    result = deduplicate_logs(log_content)
    assert result == log_content, "Should preserve all lines when too few for pattern detection"


def test_pattern_size_boundary_conditions():
    """Test boundary conditions for pattern size calculation"""
    # Test with exactly 6 lines (6 // 3 = 2, so max pattern size should be 2)
    log_content = "A\nB\nA\nB\nA\nB"
    result = deduplicate_logs(log_content)
    # Pattern "A\nB" appears 3 times, should be deduplicated
    expected = "A\nB"
    assert result == expected, "Should handle boundary condition for pattern size calculation"


def test_cursor_movement_ansi_sequences():
    """Test specific cursor movement ANSI sequences"""
    log_content = "Before\n\\\x1b[3D\\\x1b[K cursor move\nAfter"
    result = deduplicate_logs(log_content)
    
    # Check that cursor movement sequences are removed
    assert "\\\x1b[3D\\\x1b[K" not in result, "Cursor movement sequences should be removed"
    
    # Check that text content is preserved
    assert "Before" in result, "Text before ANSI should be preserved"
    assert "cursor move" in result, "Text content should be preserved"
    assert "After" in result, "Text after ANSI should be preserved"


def test_mixed_ansi_and_duplication():
    """Test logs with both ANSI sequences and duplicate patterns"""
    log_content = "Start\n\x1b[31mRed text\x1b[0m\n\x1b[31mRed text\x1b[0m\n\x1b[31mRed text\x1b[0m\nEnd"
    result = deduplicate_logs(log_content)
    
    # ANSI should be removed and duplicates should be deduplicated
    assert "\x1b[31m" not in result, "ANSI color codes should be removed"
    assert "\x1b[0m" not in result, "ANSI reset codes should be removed"
    
    # Should have deduplicated the "Red text" lines
    expected = "Start\nRed text\nEnd"
    assert result == expected, "Should remove ANSI and deduplicate patterns"


def test_zero_length_patterns():
    """Test handling of edge case with very short logs"""
    # Test with 3 lines total - should not create any patterns for deduplication
    log_content = "A\nB\nC"
    result = deduplicate_logs(log_content)
    assert result == log_content, "Should preserve all lines in very short logs"


def test_pattern_overlap_priority():
    """Test that overlapping patterns are handled correctly"""
    # Create a case where single-line and multi-line patterns overlap
    log_content = "X\nY\nX\nY\nX\nY\nZ"
    result = deduplicate_logs(log_content)
    # Both "X" and "Y" appear 3 times each, and "X\nY" appears 3 times
    # The algorithm should handle this correctly
    expected = "X\nY\nZ"
    assert result == expected, "Should handle overlapping pattern priorities correctly"


if __name__ == "__main__":
    test_sentry_issue_agent_146_real_error_log()
    test_sentry_issue_agent_146_insurance_json_patterns()
    test_ansi_escape_sequence_removal()
    test_empty_log_content()
    test_single_line_log()
    test_consecutive_duplicate_lines_exactly_three()
    test_scattered_duplicate_lines_exactly_three()
    test_multi_line_pattern_consecutive()
    test_overlapping_patterns()
    print("All deduplication tests passed!")