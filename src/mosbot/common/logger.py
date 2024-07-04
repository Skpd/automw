import logging
from logging.handlers import SysLogHandler
from logging import StreamHandler
import sys


def get_logger(name, verbose=False, stdout=True, syslog=False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    if getattr(logger, 'init', None):
        return logger

    log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    if stdout:
        stdout_handler = StreamHandler(sys.stdout)
        stdout_handler.setFormatter(log_format)
        logger.addHandler(stdout_handler)

    if syslog:
        syslog_handler = SysLogHandler()
        syslog_handler.setFormatter(log_format)
        logger.addHandler(syslog_handler)

    logger.init = True

    return logger
