from typing import Literal

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# "ours"   = produced inside GitAuto-controlled infrastructure (our Lambda, our CodeBuild, etc.) — we can edit GitAuto source to fix it, never touch customer CI.
# "theirs" = produced inside customer infrastructure (their CircleCI / GitHub Actions / Codecov run) — we fix by editing customer code or their CI config, never by editing GitAuto infrastructure.
LogOwnership = Literal["ours", "theirs"]

_OWNERSHIP_HEADERS: dict[LogOwnership, str] = {
    "ours": "OUR infrastructure (GitAuto-controlled)",
    "theirs": "CUSTOMER infrastructure (their runtime/CI)",
}


@handle_exceptions(default_return_value="", raise_on_error=False)
def label_log_source(log: str, ownership: LogOwnership, source: str):
    """Prepend a single-line runtime-provenance header to a log so the agent can't confuse our environment with a customer's.
    Real incident: Foxquilt/foxden-version-controller PR #203 — an unlabelled Lambda error got misread as a CircleCI problem, and the agent pushed `MONGOMS_DISTRO=ubuntu-22.04` into the customer's `.circleci/config.yml`.
    Saying just "CircleCI" or "Lambda" isn't enough — the agent can still flip the mapping. Every log must say outright whether it came from OUR or CUSTOMER infrastructure.
    """
    if not log:
        logger.info("label_log_source: empty log, returning empty string")
        return ""

    owner_label = _OWNERSHIP_HEADERS[ownership]
    logger.info(
        "label_log_source: tagging %d chars of log with ownership=%s source=%s",
        len(log),
        ownership,
        source,
    )
    return f"[log source: {owner_label} — {source}]\n{log}"
