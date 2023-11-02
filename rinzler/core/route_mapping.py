"""
End-point to callback mapper
"""
from typing import Dict


class RouteMapping:
    """
    RouteMapping
    """

    __routes = {}

    def __init__(self):
        self.__routes = {}

    def get(self, route: str, callback: callable) -> None:
        """
        Binds a GET route with the given callback
        """
        self.__set_route("get", {route: callback})

    def post(self, route: str, callback: callable) -> None:
        """
        Binds a POST route with the given callback
        """
        self.__set_route("post", {route: callback})

    def put(self, route: str, callback: callable) -> None:
        """
        Binds a PUT route with the given callback
        """
        self.__set_route("put", {route: callback})

    def patch(self, route: str, callback: callable) -> None:
        """
        Binds a PATCH route with the given callback
        """
        self.__set_route("patch", {route: callback})

    def delete(self, route: str, callback: callable) -> None:
        """
        Binds a PUT route with the given callback
        """
        self.__set_route("delete", {route: callback})

    def head(self, route: str, callback: callable) -> None:
        """
        Binds a HEAD route with the given callback
        """
        self.__set_route("head", {route: callback})

    def options(self, route: str, callback: callable) -> None:
        """
        Binds a OPTIONS route with the given callback
        """
        self.__set_route("options", {route: callback})

    def __set_route(self, http_method: str, route: Dict[str, callable]):
        """
        Sets the given http_method and route to the route mapping: path -> callback
        """
        if self.verify_route_already_bound(http_method, route):
            return

        if http_method not in self.__routes:
            self.__routes[http_method] = [route]
            return

        self.__routes[http_method].append(route)

    def verify_route_already_bound(self, http_method: str, route: dict) -> bool:
        """
        Checks whether or not a route is already bound to the given type_route
        :param http_method: str
        :param route: dict
        :return: bool
        """
        if http_method not in self.__routes:
            return False

        for bound_route in self.__routes[http_method]:
            bound_key = list(bound_route.keys())[0]
            route_key = list(route.keys())[0]
            if bound_key == route_key:
                return True

    def get_routes(self):
        """
        Gets the mapped routes
        :rtype: dict
        """
        return self.__routes
