"""
Shared builders for the Router integration tests.

Wiring a Router takes three pieces no test should have to assemble by hand:
an app with logging silenced, a controller following the `connect(app)`
contract, and the Router itself. They live here so each test file only talks
about what it is actually verifying.
"""

from unittest import mock

from rinzler import Rinzler
from rinzler.core.router import Router


class CallbackSpy:
    """Test double in the shape `set_response_callback` demands: has `call`."""

    def __init__(self):
        self.calls = []

    def call(self, **kwargs):
        self.calls.append(kwargs)

    @property
    def was_called(self) -> bool:
        return len(self.calls) > 0


def make_app(name="test") -> Rinzler:
    """App with logging silenced and no authentication service."""
    with mock.patch.object(Rinzler, "set_log"):
        app = Rinzler(name)
    app.log = mock.Mock()
    # Router reads `app.auth_service` in __init__; the class only annotates it.
    app.auth_service = None
    return app


def make_controller(callback, method="get", route="/ping"):
    """Controller following rinzler's contract: callable exposing `connect(app)`."""

    class Controller:
        def connect(self, app):
            routes = app.get_end_point_register()
            getattr(routes, method)(route, callback)
            return routes

    return Controller


def make_router(app, controller, route="v1") -> Router:
    return Router(app=app, route=route, controller=controller)


def make_router_raising(exception, route="v1") -> Router:
    """Router whose mapped endpoint always raises the given exception."""

    def endpoint(request, app, **params):
        raise exception

    app = make_app()
    return make_router(app, make_controller(endpoint), route=route)
