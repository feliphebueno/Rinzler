"""
CallbackResolver service module
"""
import os
import re
import logging
from collections import OrderedDict
from typing import Union, List, Tuple, Dict

from django.core.exceptions import RequestDataTooBig
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from raven.contrib.django.raven_compat.models import client

from rinzler.core.route_mapping import RouteMapping
from rinzler.core.response import Response
from rinzler.exceptions.conflict_exception import ConflictException
from rinzler.exceptions.content_too_large_exception import ContentTooLargeException
from rinzler.exceptions.gone_exception import GoneException
from rinzler.exceptions.internal_exception import InternalException
from rinzler.exceptions.invalid_input_exception import InvalidInputException
from rinzler.exceptions.auth_exception import AuthException
from rinzler.exceptions.not_allowed_exception import NotAllowedException
from rinzler.exceptions.not_found_exception import NotFoundException
from rinzler.exceptions.service_unavailable_exception import ServiceUnavailableException
from rinzler.exceptions.unacceptable_input_exception import UnacceptableInputException
from rinzler.exceptions.unauthorized_exception import UnauthorizedException


class Router(TemplateView):
    """
    Router
    """
    __request = None
    __callable = None
    __app = dict()
    __route = str()
    __end_point_uri = str()
    __uri = str()
    __method = str()
    __bound_routes = dict()
    __auth_service = None
    __response_callback = None
    __url_params_like = str()
    __url_params: Dict[str, str] = dict()
    __allowed_headers = "Authorization, Content-Type, If-Match, If-Modified-Since, If-None-Match, If-Unmodified-Since,"\
                        " Origin, X-GitHub-OTP, X-Requested-With, Content-Checksum"
    __allowed_methods = "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"

    def __init__(self, route, controller):
        super(Router, self).__init__()
        self.__route = route
        self.__callable = controller

    def flush(self):
        """
        Flushes this objects to prevent memory leaking across requests
        """
        self.__request = None
        self.__request = None
        self.__request = None
        self.__request = None
        self.__uri = None
        self.__method = None
        self.__bound_routes = dict()

    @csrf_exempt
    def route(self, request: HttpRequest):
        """
        Prepares for the CallBackResolver and handles the response and exceptions
        :param request HttpRequest
        :rtype: HttpResponse
        """
        self.flush()
        self.__request = request
        self.__uri = request.path[1:]
        self.__method = request.method
        self.__bound_routes = dict()
        self.register('log', logging.getLogger(os.urandom(3).hex().upper()))
        self.register('router', RouteMapping())

        self.__app['router'].flush_routes()
        routes = self.__callable().connect(self.__app)

        self.__bound_routes = routes['router'].get__routes()

        request_headers = request.META
        if 'HTTP_USER_AGENT' in request_headers:
            indent = 2 if re.match("[Mozilla]{7}", request_headers['HTTP_USER_AGENT']) else 0
        else:
            indent = 0

        if self.set_end_point_uri() is False:
            return self.set_response_headers(self.no_route_found(self.__request).render(indent))

        acutal_params = self.get_url_params(self.get_end_point_uri())
        response = HttpResponse(None)
        try:
            response = self.exec_route_callback(acutal_params)
        except InvalidInputException:
            client.captureException()
            self.__app['log'].error("< 400", exc_info=True)
            response = Response(None, status=400)
        except UnauthorizedException:
            client.captureException()
            self.__app['log'].error("< 401", exc_info=True)
            response = Response(None, status=401)
        except AuthException:
            client.captureException()
            self.__app['log'].error("< 403", exc_info=True)
            response = Response(None, status=403)
        except NotFoundException:
            self.__app['log'].error("< 404", exc_info=True)
            response = Response(None, status=404)
        except NotAllowedException:
            self.__app['log'].error("< 405", exc_info=True)
            response = Response(None, status=405)
        except UnacceptableInputException:
            client.captureException()
            self.__app['log'].error("< 406", exc_info=True)
            response = Response(None, status=406)
        except ConflictException:
            client.captureException()
            self.__app['log'].error("< 409", exc_info=True)
            response = Response(None, status=409)
        except GoneException:
            client.captureException()
            self.__app['log'].error("< 410", exc_info=True)
            response = Response(None, status=410)
        except RequestDataTooBig or ContentTooLargeException:
            client.captureException()
            self.__app['log'].error("< 413", exc_info=True)
            response = Response(None, status=413)
        except BaseException or InternalException:
            client.captureException()
            self.__app['log'].error("< 500", exc_info=True)
            response = Response(None, status=500)
        except ServiceUnavailableException:
            client.captureException()
            self.__app['log'].error("< 503", exc_info=True)
            response = Response(None, status=503)
        finally:
            if type(response) == Response:
                self.call_response_callback(
                    response=response, method=request.method, route=self.__route, url=self.__uri,
                    url_params_like=self.__url_params_like, url_params=self.__url_params, body=request.body,
                    app_name=routes['app_name'], auth_data=routes.get('auth_data'),
                    client_ips=self.get_client_ip(request.META)
                )
                return self.set_response_headers(response.render(indent))
            else:
                return self.set_response_headers(response)

    def exec_route_callback(self, actual_params) -> Response or object:
        """
        Executes the resolved end-point callback, or its fallback
        :param actual_params dict
        :rtype: Response or object
        """
        self.__url_params_like = str()
        self.__url_params = dict()
        if self.__method.lower() in self.__bound_routes:
            for bound in self.__bound_routes[self.__method.lower()]:

                route = list(bound)[0]
                expected_params = self.get_url_params(route)

                if self.request_matches_route(self.get_end_point_uri(), route):
                    self.__app['log'].info("> {0} {1}".format(self.__method, self.__uri))
                    authenticate = self.authenticate(route, actual_params)
                    if authenticate:
                        self.__app['log'].debug(
                            "%s(%d) %s" % ("body ", len(self.__request.body), self.__request.body.decode('utf-8'))
                        )
                        pattern_params = self.get_callback_pattern(expected_params, actual_params)
                        self.__url_params_like = route
                        self.__url_params = pattern_params
                        return bound[route](self.__request, self.__app, **pattern_params)
                    else:
                        return authenticate

        if self.__method == "OPTIONS":
            self.__app['log'].info("Route matched: {0} {1}".format(self.__method, self.__uri))
            return self.default_route_options(self.__request)

        if self.__route == '' and self.__uri == '':
            return self.welcome_page(self.__request)
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

    def authenticate(self, bound_route, actual_params) -> object:
        """
        Runs the pre-defined authenticaton method
        :param bound_route str route matched
        :param actual_params dict actual url parameters
        :rtype: object
        """
        if self.__auth_service is not None:
            auth_route = "{0}_{1}{2}".format(self.__method, self.__route, bound_route)
            auth_data = self.__auth_service.authenticate(self.__request, auth_route, actual_params)
            self.__app['auth_data'] = auth_data

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
    def get_url_params(end_point):
        """
        Gets route parameters as dictionary
        :param end_point str target route
        :rtype: dict
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

    def set_end_point_uri(self):
        """
        Gets the route from the accessed URL
        :rtype: str
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

    def welcome_page(self, request):
        """
        Defaulf welcome page when the route / is note mapped yet
        :param request
        :rtype: HttpResponse
        """
        message = "HTTP/1.1 200 OK RINZLER FRAMEWORK"
        return HttpResponse(
            "<center><h1>{0}({1})</h1></center>".format(message, self.__app['app_name']),
            content_type="text/html", charset="utf-8"
        )

    @staticmethod
    def default_route_options(request: HttpRequest):
        """
        Default callback for OPTIONS request
        :param request HttpRequest
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
            'access-control-allow-headers': self.__allowed_headers,
            'access-control-allow-methods': self.__allowed_methods,
            'access-control-allow-origin': "*",
            'access-control-allow-credentials': True,
            'www-authenticate': "Bearer",
            'server-public-name': public_name if public_name is not None else "No one",
            'user-info': "Rinzler Framework rulez!"
        }

        for key in response_headers:
            response[key] = response_headers[key]

        status = response.status_code
        if status != 404:
            self.__app['log'].info("< {0}".format(status))

        return response

    def auth_config(self, auth_service: object):
        """
        Sets the authenticator service.
        :param auth_service object
        :rtype: Router
        """
        self.__auth_service = auth_service
        return self

    def register(self, name: str, handler: object, force=False):
        """
        Registers a sevico to the APP object
        :param name: str
        :param handler: object
        :param force: bool
        :return: self
        """
        if name in self.__app:
            if force is True:
                self.__app[name] = handler
        else:
            self.__app[name] = handler

        return self

    def response_callback_config(self, callback: object):
        """
        Sets the authenticator service.
        :param callback object
        :rtype: Router
        """
        self.__response_callback = callback
        return self

    def call_response_callback(self, **kwargs) -> bool:
        """
        Calls the response callback configured to this instance
        :param kwargs: the parameters you'd like to pass
        :rtype: bool
        """
        if self.__response_callback:
            self.__response_callback.call(**kwargs)

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
