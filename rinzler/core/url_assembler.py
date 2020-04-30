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
    response_callback = None

    def mount(self, route, callback):
        """
        Mounts a route with the given params
        :rtype: urls
        """
        return url(
            r'{0}'.format(route),
            Router(route, callback)
                .register('app_name', self.app_name)
                .auth_config(self.auth_service)
                .response_callback_config(self.response_callback)
                .route
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

    def set_response_callback(self, callback):
        """
        Sets a callback to be called after every Response
        """
        self.response_callback = callback
        return self
