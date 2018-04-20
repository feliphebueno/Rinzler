"""
Base service for authenticating rinzler's requests
"""
from django.http.request import HttpRequest


class BaseAuthService(object):
    """
    BaseAuthService
    """
    auth_data: object = {}  # Your authenticated data goes here

    def authenticate(self, request: HttpRequest, auth_route: str, actual_params: dict) -> bool:
        """
        Your AuhtService should override this method for request authentication, otherwise means no authentication.
        :param request: HttpRequest Django's HttpRequest object
        :param auth_route: str User's resqueted route
        :param actual_params: User's url parameters
        :return: bool
        """
        if auth_route and actual_params:
            self.auth_data = {}
        return True
