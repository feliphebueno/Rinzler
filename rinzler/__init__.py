"""
Main
"""
__name__ = "Rinzler REST Framework"
__version__ = "3.0.4"
__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]
__license__ = "MIT"

from rinzler.core.app import Rinzler


def boot(app_name: str) -> Rinzler:
    """
    Start Rinzler App
    :param app_name: str Application's identifier
    :return: dict
    """
    app = Rinzler(app_name)
    app.log.info("App booted =)")

    return app


__all__ = [Rinzler, boot]
