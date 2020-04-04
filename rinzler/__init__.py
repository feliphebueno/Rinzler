import logging

from .logger.log import setup_logging
from .core.url_assembler import UrlAssembler

__name__ = "Rinzler REST Framework"
__version__ = "1.24.2"
__author__ = "Rinzler"


def boot(app_name):
    """
    Start Rinzler App
    :param app_name: str
    :return: dict
    """
    setup_logging()
    url_assembler = UrlAssembler().set_app_name(app_name)

    logger = logging.getLogger(app_name)

    logger.info("App booted =)")

    return {
        'url_assembler': url_assembler,
        'app_name': app_name,
        'log': logger
    }
