from django.conf.urls import url

from rinzler.core.router import Router


class UrlAssembler(object):
    """
    UrlAssembler
    """
    auth_service = None
    base_path = str()
    logger = object
    app_name = str()

    def mount(self, route, callback):
        """
        Mounts a route with the given params
        :rtype: urls
        """
        return url(
            r'{0}'.format(route),
            Router(route, callback).register('app_name', self.app_name).auth_config(self.auth_service).route
        )

    def set_auth_service(self, auth_service):
        """
        Sets the authentication service
        :rtype: object
        """
        self.auth_service = auth_service
        return self

    def set_app_name(self, app_name: str):
        """
        Sets the current running app's name
        :param app_name: str
        :return: self
        """
        self.app_name = app_name
        return self
