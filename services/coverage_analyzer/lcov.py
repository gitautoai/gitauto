# Standard imports
import os

# Local imports
from services.coverage_analyzer.types import CoverageReport
from utils.error.handle_exceptions import handle_exceptions


def create_coverage_report(path: str, stats: dict, level: str):
    # For directory level and empty path, then use "."
    if level == "directory" and path == "":
        path = "."

    line_coverage = round(
        (
            (stats["lines_covered"] / stats["lines_total"] * 100)
            if stats["lines_total"] > 0
            else 100
        ),
        2,
    )
    function_coverage = round(
        (
            (stats["functions_covered"] / stats["functions_total"] * 100)
            if stats["functions_total"] > 0
            else 100
        ),
        2,
    )
    branch_coverage = round(
        (
            (stats["branches_covered"] / stats["branches_total"] * 100)
            if stats["branches_total"] > 0
            else 100
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
                (
                    f"L{func[0]}:{func[1]}"
                    if len(func) == 2
                    else f"L{func[0]}-{func[1]}:{func[2]}"
                )
                for func in sorted(stats["uncovered_functions"])
            )
        ),
        "uncovered_branches": (", ".join(sorted(stats["uncovered_branches"]))),
    }


def create_empty_stats():
    return {
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


@handle_exceptions(default_return_value=[], raise_on_error=False)
def parse_lcov_coverage(lcov_content: str):

    # Tracking stats at all levels
    repo_stats = create_empty_stats()
    dir_stats = {}
    file_stats = {}

    current_file = None
    current_stats = create_empty_stats()

    print("\nParsing LCOV content")
    for line in lcov_content.splitlines():
        line = line.strip()
        # print(line)

        if line.startswith("SF:"):  # SF: Source File
            # Start of new file section
            current_file = line[3:]

            # Extract the directory and filename
            directory_name = os.path.dirname(current_file)
            file_name = os.path.basename(current_file)

            # Skip test files
            if (
                "tests" in directory_name
                or file_name.startswith("test_")
                or file_name.endswith("_test.py")
            ):
                current_file = None
                continue

            current_stats = create_empty_stats()

        elif line.startswith("FN:"):  # FN: Function name
            # Format could be either:
            parts = [part.strip() for part in line[3:].split(",")]

            if len(parts) == 2:
                # FN:<line number>,<function name>  (Jest/Vitest, Flutter format)
                line_num, func_name = parts
                current_stats["uncovered_functions"].add((int(line_num), func_name))

            elif len(parts) == 3:
                # FN:<start_line>,<end_line>,<function name>  (Python format)
                start_line, end_line, func_name = parts
                current_stats["uncovered_functions"].add(
                    (int(start_line), int(end_line), func_name)
                )
            else:
                continue  # Skip malformed lines

        elif line.startswith("FNDA:"):  # FNDA: Function execution counts
            # Format: FNDA:<execution count>,<function name>
            execution_count, function_name = line[5:].split(",")
            execution_count = int(execution_count)
            if execution_count > 0:
                current_stats["functions_covered"] += 1
                # Remove function from uncovered set by matching function name
                current_stats["uncovered_functions"] = {
                    func
                    for func in current_stats["uncovered_functions"]
                    if (func[1] if len(func) == 2 else func[2]) != function_name
                }
            current_stats["functions_total"] += 1

        elif line.startswith("FNF:"):  # FNF: Functions Found
            current_stats["functions_total"] = int(line[4:])

        elif line.startswith("FNH:"):  # FNH: Functions Hit
            current_stats["functions_covered"] = int(line[4:])

        elif line.startswith("BRDA:"):  # BRDA: Branch data
            try:
                line_num, block_num, branch_desc, taken = line[5:].split(",")
                line_num = int(line_num)
                block_num = int(block_num)

                if branch_desc.startswith("jump to line "):
                    # Format for Pytest: BRDA:<line number>,<block number>,jump to line <target>,<taken>
                    target_line = branch_desc.replace("jump to line ", "")
                    branch_info = f"line {line_num}, block {block_num}, if branch: {line_num} -> {target_line}"
                elif branch_desc.startswith("return from function "):
                    # Format for Pytest: BRDA:<line number>,<block number>,return from function '<name>',<taken>
                    func_name = branch_desc.replace(
                        "return from function '", ""
                    ).rstrip("'")
                    branch_info = (
                        f"line {line_num}, block {block_num}, return from: {func_name}"
                    )
                elif branch_desc == "exit the module":
                    # Format for Pytest: BRDA:<line number>,<block number>,exit the module,<taken>
                    branch_info = f"line {line_num}, block {block_num}, module exit"
                else:
                    # Format for Jest/Flutter: BRDA:<line number>,<block number>,<branch number>,<taken>
                    branch_num = int(branch_desc)
                    branch_info = (
                        f"line {line_num}, block {block_num}, branch {branch_num}"
                    )

                current_stats["uncovered_branches"].add(branch_info)

                if taken != "-" and int(taken) > 0:
                    current_stats["branches_covered"] += 1
                    current_stats["uncovered_branches"].discard(branch_info)
                current_stats["branches_total"] += 1
            except (ValueError, IndexError):
                print(f"Error parsing line: {line}")
                continue  # Skip malformed lines

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
                file_stats[current_file] = current_stats

                # Update directory stats
                dir_path = os.path.dirname(current_file)
                if dir_path not in dir_stats:
                    dir_stats[dir_path] = create_empty_stats()
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

            print("")

    # Second pass: generate all reports
    reports: list[CoverageReport] = []

    # Use create_coverage_report function
    for path, stats in file_stats.items():
        reports.append(create_coverage_report(path, stats, "file"))

    for path, stats in dir_stats.items():
        reports.append(create_coverage_report(path, stats, "directory"))

    reports.append(create_coverage_report("All", repo_stats, "repository"))

    return reports
