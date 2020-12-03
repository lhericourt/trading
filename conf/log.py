import logging


def setup_custom_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(pathname)s:%(lineno)d - %(message)s',
                                  '%m-%d %H:%M:%S')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger
