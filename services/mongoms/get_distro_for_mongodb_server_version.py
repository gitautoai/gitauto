from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="amazon2023", raise_on_error=False)
def get_distro_for_mongodb_server_version(mongodb_server_version: str):
    """Return a distro name whose MongoDB binary runs on our AL2023 Lambda.
    MongoDB 7.0+ has amazon2023 builds — use those.
    MongoDB 6.0.x has no amazon2023 build, so fall back to rhel90 (RHEL 9 ships glibc 2.34 and OpenSSL 3, same ABI as AL2023).
    Using `amazon2` for 6.x produces a binary linked against libcrypto.so.10 (OpenSSL 1.0.x) which AL2023 does not provide — Foxquilt PR #203 run (CloudWatch 2026-04-21 14:01:55) crashed with exactly this error.
    """
    # Extract major.minor from version strings like "v7.0-latest", "7.0.11", "6.0.14"
    cleaned = mongodb_server_version.lstrip("v")
    major_str = cleaned.split(".")[0]
    try:
        major = int(major_str)
    except ValueError:
        logger.warning(
            "get_distro_for_mongodb_server_version: can't parse major from %s, defaulting to amazon2023",
            mongodb_server_version,
        )
        return "amazon2023"

    if major >= 7:
        logger.info(
            "get_distro_for_mongodb_server_version: MongoDB %s.x uses amazon2023 distro",
            major,
        )
        return "amazon2023"

    logger.info(
        "get_distro_for_mongodb_server_version: MongoDB %s.x uses rhel90 distro (no amazon2023 build exists for 6.x; rhel90 shares glibc+OpenSSL ABI with AL2023)",
        major,
    )
    return "rhel90"
