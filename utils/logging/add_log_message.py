from utils.logging.logging_config import logger


def add_log_message(msg: str, log_messages: list[str]):
    logger.info(msg)
    log_messages.append(msg)
