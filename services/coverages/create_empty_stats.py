from services.coverages.coverage_types import CoverageStats


def create_empty_stats():
    stats: CoverageStats = {
        "lines_total": 0,
        "lines_covered": 0,
        "functions_total": 0,
        "functions_covered": 0,
        "branches_total": 0,
        "branches_covered": 0,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
    }
    return stats
