import os
from datetime import datetime
import logging


class Log(object):

    __logger = object()
    __base_path = str
    __signature = 'SYS'

    def __init__(self, base_path=str()):
        self.config_path(base_path)
        self.__base_path = base_path
        self.setup_logging()

    def setup_logging(self):
        """
        Setup logging configuration
        """
        file_name = self.get_filename()
        logging.basicConfig(
            level=logging.INFO,
            filename=file_name,
            format='%(asctime)-15s %(levelname)s %(message).500s'
        )

        self.__logger = self

    def get_filename(self):
        name = datetime.now().strftime("%Y-%m-%d")
        file_name = "{0}/{1}_access.log".format(os.path.realpath(self.__base_path), name)

        open(file_name, "a+").close()
        return file_name

    @staticmethod
    def config_path(path: str()):

        if os.path.exists(path) is not True:
            os.mkdir(path)
            if os.path.exists(path) is not True:
                raise RuntimeWarning(
                    "O path informado({0}) para o log não existe ou não permite leitura/escrita."\
                    .format(path)
                )
        return True

    def get_logger(self):
        return self.__logger

    def set_signature(self, sign: str()):
        self.__signature = sign
        return self

    def debug(self, msg, *args, **kwargs):
        return logging.debug("{0}: {1}".format(self.__signature, msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return logging.info("{0}: {1}".format(self.__signature, msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return logging.warning("{0}: {1}".format(self.__signature, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return logging.error("{0}: {1}".format(self.__signature, msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        return logging.critical("{0}: {1}".format(self.__signature, msg), *args, **kwargs)
