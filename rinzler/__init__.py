"""
Main
"""
from typing import Union, Tuple, List, Dict

from django.core.exceptions import RequestDataTooBig

__name__ = "Rinzler REST Framework"
__version__ = "2.2.1"
__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]

import os
import re
from datetime import datetime
from collections import OrderedDict
from logging import Logger, getLogger

from django.http import HttpResponse
from django.http.request import HttpRequest
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import url

from raven.contrib.django.raven_compat.models import client


from rinzler.auth.base_auth_service import BaseAuthService
from rinzler.logger.log import setup_logging
from rinzler.core.route_mapping import RouteMapping
from rinzler.core.response import Response
from rinzler.exceptions.auth_exception import AuthException
from rinzler.exceptions import RinzlerHttpException


class Rinzler(object):
    """
    Rinzler's object main class
    """
    request_handle_time = None
    log: Logger = None
    app_name: str = None
    auth_service: BaseAuthService = None
    response_callback: callable = None
    auth_data = dict()
    allowed_headers = "Authorization, Content-Type, If-Match, If-Modified-Since, If-None-Match, If-Unmodified-Since,"\
        " Origin, X-GitHub-OTP, X-Requested-With, Content-Checksum"
    allowed_methods = "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"
    allowed_origins = "*"
    default_headers = dict()

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.set_log()

    def mount(self, route: str, controller: callable) -> url:
        """
        Maps a route namespace with the given params and point it's requests to the especified controller.
        :param route: str Namespace route to be mapped
        :param controller: callback Controller callable to map end-points
        :rtype: url
        """
        if issubclass(controller, TemplateView):
            return url(
                r"%s" % route,
                Router(self, route, controller).handle
            )
        else:
            raise TypeError("The controller %s must be a subclass of %s" % (
                    controller, TemplateView
                )
            )

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
        self.log = getLogger(self.app_name)
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
        if hasattr(callback, 'call'):
            self.response_callback = callback
            return self
        else:
            raise TypeError("Your callback must have a call method")


class Router(TemplateView):
    """
    Router
    """
    app: Rinzler = None
    __request_start: datetime = None
    __request: HttpRequest = None
    __controller: callable = None
    __route = str()
    __end_point_uri = str()
    __uri = str()
    __method = str()
    __end_points = dict()
    __auth_service: BaseAuthService = None
    __url_params_like = str()
    __url_params: Dict[str, str] = dict()

    def __init__(self, app: Rinzler, route, controller):
        super(Router, self).__init__()
        self.app = app
        self.__route = route
        self.__controller = controller
        self.__auth_service = app.auth_service

    @csrf_exempt
    def handle(self, request: HttpRequest) -> HttpResponse:
        """
        Prepares for the CallBackResolver and handles the response and exceptions
        :param request HttpRequest
        :rtype: HttpResponse
        """
        self.__request_start = datetime.now()
        self.__request = request
        self.__uri = request.path[1:]
        self.__method = request.method

        # Initializes the callable controller and call it's connect method to get the mapped end-points.
        controller: RouteMapping = self.__controller().connect(self.app)

        self.__end_points = controller.get_routes()

        indent = self.get_json_ident(request.META)

        if self.set_end_point_uri() is False:
            return self.set_response_headers(self.no_route_found(self.__request).render(indent))

        response = HttpResponse(None)
        try:
            response = self.exec_route_callback()
        except RinzlerHttpException as e:
            client.captureException()
            self.app.log.error(f"< {e.status_code}", exc_info=True)
            response = Response(None, status=e.status_code)
        except RequestDataTooBig:
            client.captureException()
            self.app.log.error("< 413", exc_info=True)
            response = Response(None, status=413)
        except BaseException:
            client.captureException()
            self.app.log.error("< 500", exc_info=True)
            response = Response(None, status=500)
        finally:
            if type(response) == Response:
                self.call_response_callback(
                    response=response, method=request.method, route=self.__route, url=self.__uri,
                    url_params_like=self.__url_params_like, url_params=self.__url_params, body=request.body,
                    app_name=self.app.app_name, auth_data=self.app.auth_data,
                    client_ips=self.get_client_ip(request.META)
                )
                return self.set_response_headers(response.render(indent))
            else:
                return self.set_response_headers(response)

    def exec_route_callback(self) -> Response or object:
        """
        Executes the resolved end-point callback, or its fallback
        :rtype: Response or object
        """
        self.__url_params_like = str()
        self.__url_params = dict()
        if self.__method.lower() in self.__end_points:
            for bound in self.__end_points[self.__method.lower()]:

                route = list(bound)[0]
                expected_params = self.get_url_params(route)
                actual_params = self.get_url_params(self.get_end_point_uri())

                if self.request_matches_route(self.get_end_point_uri(), route):
                    self.app.log.info("> {0} {1}".format(self.__method, self.__uri))
                    if self.authenticate(route, actual_params):
                        self.app.log.debug(
                            "%s(%d) %s" % ("body ", len(self.__request.body), self.__request.body.decode('utf-8'))
                        )
                        pattern_params = self.get_callback_pattern(expected_params, actual_params)
                        self.app.request_handle_time = (
                            lambda d: int((d.days * 24 * 60 * 60 * 1000) + (d.seconds * 1000) + (d.microseconds / 1000))
                        )(datetime.now() - self.__request_start)
                        self.__url_params_like = route
                        self.__url_params = pattern_params

                        return bound[route](self.__request, self.app, **pattern_params)
                    else:
                        raise AuthException("Authentication failed.")

        if self.__method == "OPTIONS":
            self.app.log.info("Route matched: {0} {1}".format(self.__method, self.__uri))
            return self.default_route_options()

        if self.__route == '' and self.__uri == '':
            return self.welcome_page()
        else:
            return self.no_route_found(self.__request)

    def request_matches_route(self, actual_route: str, expected_route: str):
        """
        Determines whether a route matches the actual requested route or not
        :param actual_route str
        :param expected_route
        :rtype: Boolean
        """
        expected_params = self.get_url_params(expected_route)
        actual_params = self.get_url_params(actual_route)
        i = 0

        if len(expected_params) == len(actual_params):
            for param in actual_params:
                if expected_params[i][0] != "{":
                    if param != expected_params[i]:
                        return False
                i += 1
        else:
            return False

        return True

    def authenticate(self, bound_route, actual_params) -> bool:
        """
        Runs the pre-defined authenticaton service
        :param bound_route str route matched
        :param actual_params dict actual url parameters
        :rtype: bool
        """
        if self.__auth_service is not None:
            auth_route = "{0}_{1}{2}".format(self.__method, self.__route, bound_route)
            auth_data = self.__auth_service.authenticate(self.__request, auth_route, actual_params)
            if auth_data is True:
                self.app.auth_data = self.__auth_service.auth_data
            else:
                return False

        return True

    @staticmethod
    def get_callback_pattern(expected_params, actual_params):
        """
        Assembles a dictionary whith the parameters schema defined for this route
        :param expected_params dict parameters schema defined for this route
        :param actual_params dict actual url parameters
        :rtype: dict
        """
        pattern = dict()
        key = 0
        for exp_param in expected_params:
            if exp_param[0] == '{' and exp_param[-1:] == '}':
                pattern[exp_param[1:-1]] = actual_params[key]
            key = key + 1
        return pattern

    @staticmethod
    def get_url_params(end_point: str) -> list:
        """
        Gets route parameters as dictionary
        :param end_point str target route
        :rtype: list
        """
        var_params = end_point.split('/')

        if len(var_params) == 1 and var_params[0] == '':
            return []

        elif len(var_params) == 1 and var_params[0] != '':
            return [var_params[0]]
        else:
            params = list()
            for param in var_params:
                if len(param) > 0:
                    params.append(param)
            return params

    def get_end_point_uri(self):
        """
        Returns the value of __end_point_uri
        :rtype: str
        """
        return self.__end_point_uri

    def set_end_point_uri(self) -> bool:
        """
        Extracts the route from the accessed URL and sets it to __end_point_uri
        :rtype: bool
        """
        expected_parts = self.__route.split("/")
        actual_parts = self.__uri.split("/")

        i = 0
        for part in expected_parts:
            if part != actual_parts[i]:
                return False
            i = i + 1

        uri_prefix = len(self.__route)
        self.__end_point_uri = self.__uri[uri_prefix:]
        return True

    def no_route_found(self, request):
        """
        Default callback for route not found
        :param request HttpRequest
        :rtype: Response
        """
        response_obj = OrderedDict()
        response_obj["status"] = False
        response_obj["exceptions"] = {
            "message": "No route found for {0} {1}".format(self.__method, self.__uri),
        }
        response_obj["request"] = {
            "method": self.__method,
            "path_info": self.__uri,
            "content": request.body.decode("utf-8")
        }
        response_obj["message"] = "We are sorry, but something went terribly wrong."

        return Response(response_obj, content_type="application/json", status=404, charset="utf-8")

    def welcome_page(self):
        """
        Defaulf welcome page when the route / is note mapped yet
        :rtype: HttpResponse
        """
        message = "HTTP/1.1 200 OK RINZLER FRAMEWORK"
        return HttpResponse(
            "<center><h1>{0}({1})</h1></center>".format(message, self.app.app_name),
            content_type="text/html", charset="utf-8"
        )

    @staticmethod
    def default_route_options():
        """
        Default callback for OPTIONS request
        :rtype: Response
        """
        response_obj = OrderedDict()

        response_obj["status"] = True
        response_obj["data"] = "Ok"

        return Response(response_obj, content_type="application/json", charset="utf-8")

    def set_response_headers(self, response: HttpResponse) -> HttpResponse:
        """
        Appends default headers to every response returned by the API
        :param response HttpResponse
        :rtype: HttpResponse
        """
        public_name = os.environ.get('SERVER_PUBLIC_NAME')
        response_headers = {
            'access-control-allow-headers': self.app.allowed_headers,
            'access-control-allow-methods': self.app.allowed_methods,
            'access-control-allow-origin': self.app.allowed_origins,
            'access-control-allow-credentials': True,
            'www-authenticate': "Bearer",
            'server-public-name': public_name if public_name else "No one",
            'user-info': "Rinzler Framework rulez!"
        }

        response_headers.update(self.app.default_headers)

        for key in response_headers:
            response[key] = response_headers[key]

        status = response.status_code
        if status != 404:
            self.app.log.info("< {0}".format(status))

        return response

    @staticmethod
    def get_json_ident(request_headers: dict) -> int:
        """
        Defines whether the JSON response will be indented or not
        :param request_headers: dict
        :return: self
        """
        if 'HTTP_USER_AGENT' in request_headers:
            indent = 2 if re.match("[Mozilla]{7}", request_headers['HTTP_USER_AGENT']) else 0
        else:
            indent = 0

        return indent

    def call_response_callback(self, **kwargs) -> bool:
        """
        Calls the response callback configured to this instance
        :param kwargs: the parameters you'd like to pass
        :rtype: bool
        """
        if self.app.response_callback:
            self.app.response_callback.call(**kwargs)

        return True

    @staticmethod
    def get_client_ip(meta: dict) -> Union[Tuple[List[str], str, str], None]:
        """
        Returns the client ip address from the request headers
        Return the headers: HTTP_X_FORWARDED_FOR, HTTP_X_REAL_IP, REMOTE_ADDR
        """
        try:
            ip_f = meta.get("HTTP_X_FORWARDED_FOR", None)
            ip_list = list()
            if ip_f:
                ip_list: List[str] = [i.strip() for i in ip_f.split(",")]

            return ip_list, meta.get("HTTP_X_REAL_IP"), meta.get("REMOTE_ADDR")
        except (KeyError, IndexError):
            return None


def boot(app_name) -> Rinzler:
    """
    Start Rinzler App
    :param app_name: str Application's identifier
    :return: dict
    """
    app = Rinzler(app_name)
    app.log.info("App booted =)")

    return app
