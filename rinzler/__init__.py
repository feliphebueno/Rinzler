import logging

from .logger.log import setup_logging
from .core.url_assembler import UrlAssembler

__name__ = "Rinzler REST Framework"
__version__ = "1.12.0"
__author__ = "Rinzler"


def boot(app_name):
    setup_logging()
    url_assembler = UrlAssembler().set_app_name(app_name)

    logging.getLogger(app_name).info("App booted =)")

    return {
        'url_assembler': url_assembler,
        'app_name': app_name
    }
