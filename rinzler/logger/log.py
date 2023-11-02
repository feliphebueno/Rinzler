from logging import config as log_config
import os

import yaml

from rinzler.logger import default_config


def setup_logging(default_path="logging.yaml", env_key="LOG_CFG"):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value

    if os.path.exists(path):
        with open(path, "rt") as f:
            custom_config = yaml.safe_load(f.read())
        log_config.dictConfig(custom_config)
    else:
        log_config.dictConfig(default_config)
