import re


def deduplicate_logs(log_content: str) -> str:
    # Remove ANSI escape sequences (terminal formatting codes with no semantic value)
    ansi_sequences = [
        r"\\\x1b\[\d+D\\\x1b\[K",  # Cursor movement sequences
        r"\x1b\[[0-9;]+m",  # All ANSI color/formatting codes
    ]

    for pattern in ansi_sequences:
        log_content = re.sub(pattern, "", log_content)

    lines = log_content.split("\n")

    # Find all repetitive patterns using rolling hash
    pattern_occurrences = {}

    # Check patterns of different sizes
    for size in range(1, min(20, len(lines) // 3) + 1):
        for i in range(len(lines) - size + 1):
            pattern = tuple(lines[i : i + size])
            if pattern not in pattern_occurrences:
                pattern_occurrences[pattern] = []
            pattern_occurrences[pattern].append(i)

    # Find patterns that repeat 3+ times (consecutive OR scattered)
    to_remove = set()
    for pattern, positions in pattern_occurrences.items():
        if len(positions) < 3:
            continue

        size = len(pattern)

        # Handle consecutive repetitions (original logic)
        consecutive_groups = []
        current_group = [positions[0]]

        for pos in positions[1:]:
            if pos == current_group[-1] + size:
                current_group.append(pos)
            else:
                if len(current_group) >= 3:
                    consecutive_groups.append(current_group)
                current_group = [pos]

        if len(current_group) >= 3:
            consecutive_groups.append(current_group)

        # Mark consecutive repetitions for removal (keep first occurrence)
        for group in consecutive_groups:
            for pos in group[1:]:  # Skip first occurrence
                for j in range(size):
                    to_remove.add(pos + j)

        # Handle scattered repetitions (new logic)
        # If pattern appears 3+ times scattered, keep only first occurrence
        # Only apply scattered logic if no consecutive groups were found
        if len(positions) >= 3 and not consecutive_groups:
            for pos in positions[1:]:  # Keep first 1, remove rest
                for j in range(size):
                    to_remove.add(pos + j)

    # Build result excluding removed positions
    result = []
    for i, line in enumerate(lines):
        if i not in to_remove:
            result.append(line)

    return "\n".join(result)
