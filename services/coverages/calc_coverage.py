from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def calc_coverage(covered: int | None, total: int | None):
    # None total = tool doesn't measure this metric (e.g. phpunit doesn't report branches)
    if total is None:
        return None

    # 0 total = tool measures it but found 0 (e.g. Jest BRF:0) = nothing to cover = 100%
    if total == 0:
        return 100

    # Normal case: covered / total
    return round((covered or 0) / total * 100, 1)
