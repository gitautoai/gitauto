# Standard imports
import os

# Local imports
from config import UTF8
from services.coverage_analyzer.types import CoverageReport
from utils.file_manager import run_command
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def calculate_dart_coverage(local_path: str):
    # Set up Flutter in /tmp
    tmp_flutter = "/tmp/flutter"
    print(f"\nCopying Flutter to {tmp_flutter}")
    os.makedirs(tmp_flutter, exist_ok=True)
    os.system(f"cp -r /usr/local/flutter/* {tmp_flutter}/")

    # Set environment variables for Flutter
    env = os.environ.copy()
    env["PATH"] = f"{tmp_flutter}/bin:{env.get('PATH', '')}"
    env["FLUTTER_ROOT"] = tmp_flutter

    # Debug: Print current PATH and check Flutter binary
    print(f"\nCurrent PATH: {env['PATH']}")
    print(f"Flutter binary exists: {os.path.exists(f'{tmp_flutter}/bin/flutter')}")

    # Run flutter test command
    print("\nRunning `flutter test --coverage`")
    result = run_command(
        cwd=local_path,
        command="flutter test --coverage",
        use_shell=True,
        env=env,
    )
    print(f"Flutter test result stdout:\n{result.stdout}")

    # Check if the command failed
    if result.returncode != 0:
        print(f"Flutter test error:\n{result.stderr}")
        return []

    # Get the coverage directory
    coverage_dir = os.path.join(local_path, "coverage")
    if not os.path.exists(coverage_dir):
        print(f"No coverage directory found at {coverage_dir}")
        return []

    # Parse lcov.info
    lcov_path = os.path.join(coverage_dir, "lcov.info")
    if os.path.exists(lcov_path):
        return parse_lcov_coverage(lcov_path)

    print("No coverage report files found")
    return []


@handle_exceptions(default_return_value=[], raise_on_error=False)
def parse_lcov_coverage(lcov_path: str):
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

    print(f"\nParsing LCOV file: {lcov_path}")
    with open(lcov_path, "r", encoding=UTF8) as f:
        for line in f:
            line = line.strip()
            print(line)

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

    # File level reports
    for path, stats in file_stats.items():
        reports.append(create_coverage_report(path, stats, "file"))

    # Directory level reports
    for path, stats in dir_stats.items():
        reports.append(create_coverage_report(path, stats, "directory"))

    # Repository level report
    reports.append(create_coverage_report("All", repo_stats, "repository"))

    return reports
