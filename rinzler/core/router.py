import os
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from rinzler.core.app import Rinzler
from rinzler.auth.base_auth_service import BaseAuthService
from rinzler.core.response import Response
from rinzler.core.route_mapping import RouteMapping
from rinzler.exceptions import RinzlerHttpException
from rinzler.exceptions.auth_exception import AuthException


class Router(View):
    """
    Router
    """

    app: Rinzler = None
    controller: callable = None
    route = ""
    __request_start: datetime = None
    __end_point_uri = ""
    __end_points = {}
    __auth_service: BaseAuthService = None

    def __init__(self, app: Rinzler, route, controller):
        super(Router, self).__init__()
        self.app = app
        self.route = route
        self.controller = controller
        self.__auth_service = app.auth_service

    @csrf_exempt
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Prepares for the CallBackResolver and handles the response and exceptions
        :param request HttpRequest
        :rtype: HttpResponse
        """
        self.__request_start = datetime.now()
        uri = request.path[1:]
        route_path = f"{request.method} {uri}"

        # Initializes the callable controller and calls its connect method to get the mapped end-points.
        controller: RouteMapping = self.controller().connect(self.app)

        self.__end_points = controller.get_routes()

        indent = self.get_json_ident(request.META)

        if self.set_end_point_uri(uri) is False:
            return self.set_response_headers(self.no_route_found(request, uri).render(indent))

        actual_params = self.get_url_params(self.get_end_point_uri())
        response = HttpResponse(None)
        url_params_like = ""
        url_params: Dict[str, str] = {}
        try:
            response, url_params_like, url_params = self.exec_route_callback(request, uri, actual_params)
        except RinzlerHttpException as e:
            self.app.log.exception(f"< {e.status_code} {route_path}")
            response = Response(None, status=e.status_code)
        except RequestDataTooBig:
            self.app.log.exception(f"< 413 {route_path}")
            response = Response(None, status=413)
        except BaseException:
            self.app.log.exception(f"< 500 {route_path}")
            response = Response(None, status=500)
        finally:
            self.call_response_callback(
                response=response,
                method=request.method,
                route=self.route,
                url=uri,
                url_params_like=url_params_like,
                url_params=url_params,
                body=request.body,
                app_name=self.app.app_name,
                auth_data=self.get_authentication_data(url_params_like, actual_params, request),
                client_ips=self.get_client_ip(request.META),
            )

            response_body = response.render(indent) if isinstance(response, Response) else response
            response = self.set_response_headers(response_body)

        return response

    def exec_route_callback(
        self, request: HttpRequest, uri: str, actual_params: List[str]
    ) -> Tuple[Union[Response, object], Any, Any]:
        """
        Executes the resolved end-point callback, or its fallback
        :param request: HttpRequest actual request, coming from Django
        :param uri: str url of the actual request
        :param actual_params: List[str]
        :rtype: Response or object
        """
        method = request.method
        if method.lower() in self.__end_points:
            for bound in self.__end_points[method.lower()]:
                route = list(bound)[0]
                expected_params = self.get_url_params(route)

                if self.request_matches_route(self.get_end_point_uri(), route):
                    self.app.log.info("> {0} {1}".format(method, uri))

                    if not self.authenticate(route, actual_params, request):
                        raise AuthException("Authentication failed.")

                    self.app.log.debug("%s(%d) %s" % ("body ", len(request.body), request.body.decode("utf-8")))
                    pattern_params = self.get_callback_pattern(expected_params, actual_params)
                    self.app.request_handle_time = (
                        lambda d: int((d.days * 24 * 60 * 60 * 1000) + (d.seconds * 1000) + (d.microseconds / 1000))
                    )(datetime.now() - self.__request_start)

                    return (
                        bound[route](request, self.app, **pattern_params),
                        route,
                        pattern_params,
                    )

        if method == "OPTIONS":
            self.app.log.info("Route matched: {0} {1}".format(method, uri))
            return self.default_route_options(), None, None

        if self.route == "" and uri == "":
            return self.welcome_page(), None, None
        else:
            return self.no_route_found(request, uri), None, None

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

        if len(expected_params) != len(actual_params):
            return False

        for param in actual_params:
            if expected_params[i][0] != "{":
                if param != expected_params[i]:
                    return False
            i += 1

        return True

    def authenticate(self, bound_route, actual_params, request: HttpRequest) -> bool:
        """
        Runs the pre-defined authentication service
        :param bound_route str route matched
        :param actual_params dict actual url parameters
        :param request: HttpRequest request, coming from Django
        :rtype: bool
        """
        if not self.__auth_service:
            return True

        auth_route = f"{request.method}_{self.route}{bound_route}"
        if not self.__auth_service.authenticate(request, auth_route, actual_params):
            return False

        self.app.auth_data = self.__auth_service.auth_data
        return True

    def get_authentication_data(self, bound_route, actual_params, request: HttpRequest) -> Union[dict, None]:
        """
        Runs the pre-defined authentication service
        :param bound_route str route matched
        :param actual_params dict actual url parameters
        :param request: HttpRequest request, coming from Django
        :rtype: bool
        """
        if not self.__auth_service or not bound_route:
            return None

        auth_route = f"{request.method}_{self.route}{bound_route}"
        if not self.__auth_service.authenticate(request, auth_route, actual_params):
            return None

        return self.__auth_service.auth_data

    @staticmethod
    def get_callback_pattern(expected_params, actual_params):
        """
        Assembles a dictionary whith the parameters schema defined for this route
        :param expected_params dict parameters schema defined for this route
        :param actual_params dict actual url parameters
        :rtype: dict
        """
        pattern = {}
        key = 0
        for exp_param in expected_params:
            if exp_param[0] == "{" and exp_param[-1:] == "}":
                pattern[exp_param[1:-1]] = actual_params[key]
            key = key + 1
        return pattern

    @staticmethod
    def get_url_params(end_point: str) -> List[str]:
        """
        Gets route parameters as dictionary
        :param end_point str target route
        :rtype: list
        """
        var_params = end_point.split("/")

        if len(var_params) == 1 and var_params[0] == "":
            return []

        elif len(var_params) == 1 and var_params[0] != "":
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

    def set_end_point_uri(self, uri: str) -> bool:
        """
        Extracts the route from the accessed URL and sets it to __end_point_uri
        :params uri: url of the actual request
        :rtype: bool
        """
        expected_parts = self.route.split("/")
        actual_parts = uri.split("/")

        i = 0
        for part in expected_parts:
            if part != actual_parts[i]:
                return False
            i += 1

        uri_prefix = len(self.route)
        self.__end_point_uri = uri[uri_prefix:]
        return True

    @staticmethod
    def no_route_found(request, uri: str) -> Response:
        """
        Default callback for route not found
        :param request HttpRequest
        :param uri: str
        :rtype: Response
        """
        if not settings.DEBUG:
            return Response(None, status=404)

        response_data = {
            "status": False,
            "exceptions": {
                "message": "No route found for {0} {1}".format(request.method, uri),
            },
            "request": {
                "method": request.method,
                "path_info": uri,
                "content": request.body.decode("utf-8"),
            },
            "message": "We are sorry, but something went terribly wrong.",
        }

        return Response(response_data, content_type="application/json", status=404)

    def welcome_page(self):
        """
        Defaulf welcome page when the route / is not mapped yet
        :rtype: HttpResponse
        """
        message = "HTTP/1.1 200 OK RINZLER FRAMEWORK"
        return HttpResponse(
            "<center><h1>{0}({1})</h1></center>".format(message, self.app.app_name),
            content_type="text/html",
            charset="utf-8",
        )

    @staticmethod
    def default_route_options():
        """
        Default callback for OPTIONS request
        :rtype: Response
        """
        return Response({"status": True, "data": "Ok"}, content_type="application/json", charset="utf-8")

    def set_response_headers(self, response: HttpResponse) -> HttpResponse:
        """
        Appends default headers to every response returned by the API
        :param response HttpResponse
        :rtype: HttpResponse
        """
        response_headers = {
            "access-control-allow-headers": self.app.allowed_headers,
            "access-control-allow-methods": self.app.allowed_methods,
            "access-control-allow-origin": self.app.allowed_origins,
            "access-control-allow-credentials": True,
            "www-authenticate": "Bearer",
            "server-public-name": os.environ.get("SERVER_PUBLIC_NAME", "No one"),
            "user-info": "Rinzler Framework!",
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
        if "HTTP_USER_AGENT" in request_headers:
            indent = 2 if re.match("[Mozilla]{7}", request_headers["HTTP_USER_AGENT"]) else 0
        else:
            indent = 0

        return indent

    def call_response_callback(self, **kwargs) -> bool:
        """
        Calls the response callback configured to this instance
        :param kwargs: the parameters you'd like to pass
        :rtype: bool
        """
        if getattr(self.app, "response_callback", None):
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
