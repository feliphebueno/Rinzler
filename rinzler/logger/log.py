import os
import logging.config

import yaml

from rinzler.logger import config


def setup_logging(default_path='logging.yaml', env_key='LOG_CFG'):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            configs = yaml.safe_load(f.read())
        logging.config.dictConfig(configs)
    else:
        logging.config.dictConfig(config)
