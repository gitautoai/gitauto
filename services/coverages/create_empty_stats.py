from services.coverages.coverage_types import CoverageStats


def create_empty_stats():
    """None = not yet seen in LCOV, distinct from 0 (measured but empty)."""

    stats: CoverageStats = {
        "lines_total": None,
        "lines_covered": None,
        "functions_total": None,
        "functions_covered": None,
        "branches_total": None,
        "branches_covered": None,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
    }
    return stats
