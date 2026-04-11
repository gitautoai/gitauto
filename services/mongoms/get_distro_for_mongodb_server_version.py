from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="amazon2023", raise_on_error=False)
def get_distro_for_mongodb_server_version(mongodb_server_version: str):
    """Return the correct Amazon Linux distro name for a MongoDB server version.
    MongoDB 7.0+ has amazon2023 builds. 6.0.x and earlier only have amazon2."""
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
        "get_distro_for_mongodb_server_version: MongoDB %s.x uses amazon2 distro", major
    )
    return "amazon2"
