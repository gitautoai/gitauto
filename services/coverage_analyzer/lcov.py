# Standard imports
import os

# Local imports
from services.coverage_analyzer.types import CoverageReport
from utils.handle_exceptions import handle_exceptions


def create_coverage_report(path: str, stats: dict, level: str):
    line_coverage = round(
        (
            (stats["lines_covered"] / stats["lines_total"] * 100)
            if stats["lines_total"] > 0
            else 0
        ),
        2,
    )
    function_coverage = round(
        (
            (stats["functions_covered"] / stats["functions_total"] * 100)
            if stats["functions_total"] > 0
            else 0
        ),
        2,
    )
    branch_coverage = round(
        (
            (stats["branches_covered"] / stats["branches_total"] * 100)
            if stats["branches_total"] > 0
            else 0
        ),
        2,
    )

    return {
        "package_name": None,
        "level": level,
        "full_path": path,
        "statement_coverage": line_coverage,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "line_coverage": line_coverage,
        "uncovered_lines": (
            ", ".join(map(str, sorted(stats["uncovered_lines"])))
            if level == "file" and line_coverage > 0
            else ""
        ),
        "uncovered_functions": (
            ", ".join(
                f"L{line}:{name}" for line, name in sorted(stats["uncovered_functions"])
            )
            if level == "file" and function_coverage > 0
            else ""
        ),
        "uncovered_branches": (
            ", ".join(
                f"L{line}B{block}:{branch}"
                for line, block, branch in sorted(stats["uncovered_branches"])
            )
            if level == "file" and branch_coverage > 0
            else ""
        ),
    }


@handle_exceptions(default_return_value=[], raise_on_error=False)
def parse_lcov_coverage(lcov_content: str):
    stats_template = {
        "lines_total": 0,
        "lines_covered": 0,
        "functions_total": 0,
        "functions_covered": 0,
        "branches_total": 0,
        "branches_covered": 0,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
        "test_name": None,
        "current_function": None,
    }

    # Tracking stats at all levels
    repo_stats = stats_template.copy()
    dir_stats = {}
    file_stats = {}

    current_file = None
    current_stats = stats_template.copy()

    print("\nParsing LCOV content")
    for line in lcov_content.splitlines():
        line = line.strip()

        if line.startswith("TN:"):  # TN: Test Name
            current_stats["test_name"] = line[3:] if line[3:] else None

        elif line.startswith("SF:"):  # SF: Source File
            # Start of new file section
            current_file = line[3:]
            current_stats = stats_template.copy()

        elif line.startswith("FN:"):  # FN: Function name
            # Format: FN:<line number>,<function name>
            line_num, func_name = line[3:].split(",")
            current_stats["uncovered_functions"].add((int(line_num), func_name))

        elif line.startswith("FNDA:"):  # FNDA: Function execution counts
            # Format: FNDA:<execution count>,<function name>
            execution_count, function_name = line[5:].split(",")
            execution_count = int(execution_count)
            if execution_count > 0:
                current_stats["functions_covered"] += 1
                # Remove function from uncovered set by matching function name
                current_stats["uncovered_functions"] = {
                    (line, name)
                    for line, name in current_stats["uncovered_functions"]
                    if name != function_name
                }
            current_stats["functions_total"] += 1

        elif line.startswith("FNF:"):  # FNF: Functions Found
            current_stats["functions_total"] = int(line[4:])

        elif line.startswith("FNH:"):  # FNH: Functions Hit
            current_stats["functions_covered"] = int(line[4:])

        elif line.startswith("BRDA:"):  # BRDA: Branch data
            # Format: BRDA:<line number>,<block number>,<branch number>,<taken>
            line_num, block_num, branch_num, taken = line[5:].split(",")
            branch_info = (int(line_num), int(block_num), int(branch_num))
            current_stats["uncovered_branches"].add(branch_info)

            if taken != "-" and int(taken) > 0:
                current_stats["branches_covered"] += 1
                current_stats["uncovered_branches"].discard(branch_info)
            current_stats["branches_total"] += 1

        elif line.startswith("BRF:"):  # BRF: Branches Found
            current_stats["branches_total"] = int(line[4:])

        elif line.startswith("BRH:"):  # BRH: Branches Hit
            current_stats["branches_covered"] = int(line[4:])

        elif line.startswith("DA:"):  # DA: Line coverage data
            # Line coverage data: DA:<line number>,<execution count>
            line_num, execution_count = map(int, line[3:].split(","))
            current_stats["lines_total"] += 1
            if execution_count > 0:
                current_stats["lines_covered"] += 1
            else:
                current_stats["uncovered_lines"].add(line_num)

        # Overrides "lines_total" if available
        elif line.startswith("LF:"):  # Lines Found
            current_stats["lines_total"] = int(line[3:])

        # Overrides "lines_covered" if available
        elif line.startswith("LH:"):  # Lines Hit
            current_stats["lines_covered"] = int(line[3:])

        elif line.startswith("end_of_record"):
            if current_file and current_stats:
                # Store file stats
                file_stats[current_file] = current_stats.copy()

                # Update directory stats
                dir_path = os.path.dirname(current_file)
                if dir_path not in dir_stats:
                    dir_stats[dir_path] = stats_template.copy()
                for key, value in current_stats.items():
                    if key in [
                        "test_name",
                        "current_function",
                    ]:  # Skip metadata fields
                        continue
                    if isinstance(value, set):
                        dir_stats[dir_path][key].update(value)
                    else:
                        dir_stats[dir_path][key] += value

                # Update repository stats
                for key, value in current_stats.items():
                    if key in [
                        "test_name",
                        "current_function",
                    ]:  # Skip metadata fields
                        continue
                    if isinstance(value, set):
                        repo_stats[key].update(value)
                    else:
                        repo_stats[key] += value

    # Second pass: generate all reports
    reports: list[CoverageReport] = []

    # Use create_coverage_report function
    for path, stats in file_stats.items():
        reports.append(create_coverage_report(path, stats, "file"))

    for path, stats in dir_stats.items():
        reports.append(create_coverage_report(path, stats, "directory"))

    reports.append(create_coverage_report("All", repo_stats, "repository"))

    return reports
