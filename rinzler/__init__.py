import os

from .logger.log import Log
from .core.url_assembler import UrlAssembler

__name__ = "Rinzler REST Framework"
__version__ = "1.12.0"
__author__ = "Rinzler"


def boot(base_path: str()):
    logger = Log(os.path.realpath(base_path) + "/log").get_logger()
    url_assembler = UrlAssembler().set_logger(logger)

    logger.info("App booted =)")

    return {
        'url_assembler': url_assembler,
        'log': logger
    }
