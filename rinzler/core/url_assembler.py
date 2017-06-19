from django.conf.urls import url

from rinzler.core.router import Router


class UrlAssembler(object):

    auth_service = None

    def mount(self, route, callback):
        return url(r'{0}'.format(route), Router(route, callback).auth_config(self.auth_service).route)

    def set_auth_service(self, auth_service):
        self.auth_service = auth_service
        return self
