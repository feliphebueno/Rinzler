"""
CallbackResolver service module
"""
import re
from collections import OrderedDict

from django.http import HttpResponse
from django.http.request import HttpRequest
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

from rinzler.core.route_mapping import RouteMapping
from rinzler.exceptions.auth_exception import AuthException
from rinzler.core.response import Response


class Router(TemplateView):
    __request = None
    __callable = None
    __app = dict()
    __route = None
    __uri = None
    __method = None
    __bound_routes = dict()
    __auth_service = None
    __allowed_headers = "Authorization, Content-Type, If-Match, If-Modified-Since, If-None-Match, If-Unmodified-Since," \
                        " Origin, X-GitHub-OTP, X-Requested-With"
    __allowed_methods = "GET,POST,HEAD,DELETE,PUT,OPTIONS"

    def __init__(self, route, controller):
        self.__route = route
        self.__callable = controller
        self.__app['router'] = RouteMapping()

    @csrf_exempt
    def route(self, request: HttpRequest):
        """
        Prepares for the CallBackResolver and handles the response and exceptions
        :param request HttpRequest
        :rtype: HttpResponse
        """
        self.__request = request
        self.__uri = request.path[1:]
        self.__method = request.method

        routes = self.__callable().connect(self.__app)

        self.__bound_routes = routes['router'].get__routes()

        end_point = self.get_end_point_uri()
        acutal_params = self.get_url_params(end_point)

        request_headers = request.META
        indent = 2 if re.match("[Mozilla]{7}", request_headers['HTTP_USER_AGENT']) else 0

        try:
            response = self.exec_route_callback(acutal_params)
            return self.set_response_headers(response.render(indent))
        except AuthException as e:
            response = Response(OrderedDict({"status": False, "message": str(e)}), content_type="application/json",
                                status=403, charset="utf-8")
            return self.set_response_headers(response.render(indent))
        except BaseException as e:
            response = Response(OrderedDict({"status": False, "message": str(e)}), content_type="application/json",
                                status=500, charset="utf-8")
            return self.set_response_headers(response.render(indent))

    def exec_route_callback(self, actual_params):
        """
        Executes the resolved end-point callback, or its fallback
        :param actual_params dict
        :rtype: Object
        """
        if self.__method.lower() in self.__bound_routes:
            for bound in self.__bound_routes[self.__method.lower()]:

                route = list(bound)[0]
                expected_params = self.get_url_params(route)

                if self.request_matches_route(self.get_end_point_uri(), route):
                    authenticate = self.authenticate(route, actual_params)
                    if authenticate:
                        pattern_params = self.get_callback_pattern(expected_params, actual_params)
                        return bound[route](self.__request, self.__app, **pattern_params)
                    else:
                        return authenticate

        if self.__method == "OPTIONS":
            return self.default_route_options(self.__request)

        return self.no_route_found(self.__request)

    def request_matches_route(self, actual_route: str(), expected_route: str()):
        """
        Determines whether a route matches the actual requested route or not
        :param actual_route str
        :param expected_route
        :rtype: Boolean
        """
        expected_params = self.get_url_params(expected_route)
        actual_params = self.get_url_params(actual_route)
        i = 0

        for param in expected_params:
            if param[0] != "{":
                if (len(actual_params) - 1) >= i:
                    if param != actual_params[i]:
                        return False
                else:
                    return False
            i += 1
        return True

    def authenticate(self, bound_route, actual_params):
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
        Gets the route from the accessed URL
        :rtype: str
        """
        uri_prefix = len(self.__route)
        return self.__uri[uri_prefix:]

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

    def set_response_headers(self, response: HttpResponse):
        """
        Appends default headers to every response sent by the API
        :param response HttpResponse
        :rtype: HttpResponse
        """
        response_headers = {
            'access-control-allow-headers': self.__allowed_headers,
            'access-control-allow-methods': self.__allowed_methods,
            'access-control-allow-origin': "*",
            'access-control-allow-credentials': True,
            'www-authenticate': "Bearer",
            'user-info': "Rinzler Framework rulez!"
        }

        for key in response_headers:
            response[key] = response_headers[key]

        return response

    def auth_config(self, auth_service: object):
        """
        Sets the authenticator service.
        :param auth_service object
        :rtype: Router
        """
        self.__auth_service = auth_service
        return self
