# Standard imports
import os

# Local imports
from services.coverage_analyzer.types import CoverageReport
from utils.handle_exceptions import handle_exceptions


def create_coverage_report(path: str, stats: dict, level: str):
    return {
        "package_name": None,
        "level": level,
        "full_path": path,
        "statement_coverage": round(
            (
                (stats["lines_covered"] / stats["lines_total"] * 100)
                if stats["lines_total"] > 0
                else 0
            ),
            2,
        ),
        "function_coverage": 0,  # Not supported in Flutter/Dart
        "branch_coverage": 0,  # Not supported in Flutter/Dart
        "line_coverage": round(
            (
                (stats["lines_covered"] / stats["lines_total"] * 100)
                if stats["lines_total"] > 0
                else 0
            ),
            2,
        ),
        "uncovered_lines": (
            ", ".join(map(str, sorted(stats["uncovered_lines"])))
            if level == "file"
            else ""
        ),
    }


@handle_exceptions(default_return_value=[], raise_on_error=False)
def parse_lcov_coverage(lcov_content: str):
    stats_template = {
        "lines_total": 0,
        "lines_covered": 0,
        "uncovered_lines": set(),
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

        if line.startswith("SF:"):  # SF: Source File
            # Start of new file section
            current_file = line[3:]
            current_stats = stats_template.copy()

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
                    if key == "uncovered_lines":
                        dir_stats[dir_path][key].update(value)
                    else:
                        dir_stats[dir_path][key] += value

                # Update repository stats
                for key, value in current_stats.items():
                    if key == "uncovered_lines":
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
