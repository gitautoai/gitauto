from typing import cast

from services.jest.coverage_types import IstanbulFileCoverage
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def validate_istanbul_file_data(raw: dict):
    """Validate raw dict has the expected Istanbul coverage structure."""
    s = raw.get("s")
    f = raw.get("f")
    b = raw.get("b")
    statement_map = raw.get("statementMap")
    fn_map = raw.get("fnMap")
    branch_map = raw.get("branchMap")
    fields = {
        "s": s,
        "f": f,
        "b": b,
        "statementMap": statement_map,
        "fnMap": fn_map,
        "branchMap": branch_map,
    }
    bad = [k for k, v in fields.items() if not isinstance(v, dict)]
    if bad:
        logger.warning(
            "Invalid Istanbul coverage structure: %s",
            ", ".join(f"{k}={fields[k]!r} ({type(fields[k]).__name__})" for k in bad),
        )
        return None

    return cast(
        IstanbulFileCoverage,
        {
            "s": s,
            "f": f,
            "b": b,
            "statementMap": statement_map,
            "fnMap": fn_map,
            "branchMap": branch_map,
        },
    )
