import logging


def setup_custom_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(pathname)s:%(lineno)d - %(message)s',
                                  '%m-%d %H:%M:%S')

    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(formatter)
    handler_stream.setLevel(logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler_stream)

    return logger
