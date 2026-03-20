from services.coverages.calc_coverage import calc_coverage


def test_calc_coverage_none_total_returns_none():
    """Tool doesn't measure this metric → None"""
    assert calc_coverage(None, None) is None
    assert calc_coverage(0, None) is None


def test_calc_coverage_zero_total_returns_100():
    """Tool measures it but found 0 → nothing to cover → 100%"""
    assert calc_coverage(0, 0) == 100
    assert calc_coverage(None, 0) == 100


def test_calc_coverage_normal():
    """Normal case: covered / total"""
    assert calc_coverage(80, 100) == 80.0
    assert calc_coverage(1, 3) == 33.3
    assert calc_coverage(2, 3) == 66.7
    assert calc_coverage(5, 7) == 71.4


def test_calc_coverage_full():
    assert calc_coverage(100, 100) == 100.0
    assert calc_coverage(10, 10) == 100.0


def test_calc_coverage_zero_covered():
    assert calc_coverage(0, 100) == 0.0
    assert calc_coverage(0, 10) == 0.0
