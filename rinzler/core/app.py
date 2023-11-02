from logging import Logger, getLogger

from django.urls import re_path

from rinzler.auth.base_auth_service import BaseAuthService
from rinzler.core.route_mapping import RouteMapping
from rinzler.logger.log import setup_logging


class Rinzler:
    """
    Rinzler's object main class
    """

    request_handle_time: int
    log: Logger
    app_name: str
    auth_service: BaseAuthService
    response_callback: callable
    auth_data = {}
    allowed_headers = (
        "Authorization, Content-Type, If-Match, If-Modified-Since, If-None-Match, If-Unmodified-Since,"
        " Origin, X-GitHub-OTP, X-Requested-With, Content-Checksum"
    )
    allowed_methods = "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"
    allowed_origins = "*"
    default_headers = {}

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.set_log()

    def mount(self, route: str, controller: callable) -> re_path:
        """
        Maps a route namespace with the given params and point it's requests to the especified controller.
        :param route: str Namespace route to be mapped
        :param controller: callback Controller callable to map end-points
        :rtype: path
        """
        from rinzler.core.router import Router  # noqa

        return re_path(r"{}".format(route), Router.as_view(app=self, route=route, controller=controller))

    @staticmethod
    def get_end_point_register() -> RouteMapping:
        """
        Returns a new instance of the RouteMapping class, which is responsible for mapping end-points on the controller
        level
        :return: RouteMapping
        """
        return RouteMapping()

    def set_log(self):
        """
        Initializes the log object
        :return: self
        """
        setup_logging()
        self.log = getLogger()
        return self

    def set_auth_service(self, auth_service: BaseAuthService):
        """
        Sets the authentication service
        :param auth_service: BaseAuthService Authentication service
        :raises: TypeError If the auth_service object is not a subclass of rinzler.auth.BaseAuthService
        :rtype: Rinzler
        """
        if issubclass(auth_service.__class__, BaseAuthService):
            self.auth_service = auth_service
            return self
        else:
            raise TypeError("Your auth service object must be a subclass of rinzler.auth.BaseAuthService.")

    def set_response_callback(self, callback: callable):
        """
        Sets the callable to call before request
        :param callback: callable
        :raises: TypeError If the callback is not a callable
        :rtype: Rinzler
        """
        if not hasattr(callback, "call"):
            raise TypeError("Your callback must have a call method")

        self.response_callback = callback
        return self
