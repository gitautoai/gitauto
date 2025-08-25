def deduplicate_repetitive_logs(log_content: str) -> str:
    lines = log_content.split("\n")

    # Find all repetitive patterns using rolling hash
    pattern_occurrences = {}

    # Check patterns of different sizes
    for size in range(1, min(20, len(lines) // 3)):
        for i in range(len(lines) - size + 1):
            pattern = tuple(lines[i : i + size])
            if pattern not in pattern_occurrences:
                pattern_occurrences[pattern] = []
            pattern_occurrences[pattern].append(i)

    # Find patterns that repeat consecutively 3+ times
    to_remove = set()
    for pattern, positions in pattern_occurrences.items():
        if len(positions) < 3:
            continue

        size = len(pattern)
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

        # Mark positions for removal (keep first occurrence)
        for group in consecutive_groups:
            for pos in group[1:]:  # Skip first occurrence
                for j in range(size):
                    to_remove.add(pos + j)

    # Build result excluding removed positions
    result = []
    for i, line in enumerate(lines):
        if i not in to_remove:
            result.append(line)

    return "\n".join(result)
