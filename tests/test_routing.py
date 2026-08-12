"""
Coverage for route mapping and resolution.

Routing is the framework's other load-bearing contract: `connect(app)` binds
paths to callbacks, and dispatch decides which callback answers a request,
what URL parameters it receives, and what happens when nothing matches. None
of it was covered.

The tests go both through the public path (dispatch) and directly at the
resolution helpers, because the helpers encode rules — placeholder matching,
segment counting — that are hard to pin down from the outside alone.
"""

import pytest
from django.test import RequestFactory

from rinzler.core.response import Response
from rinzler.core.route_mapping import RouteMapping
from rinzler.core.router import Router
from tests.helpers import make_app, make_controller, make_router

VERBS = ["get", "post", "put", "patch", "delete", "head", "options"]


# ---------------------------------------------------------------------------
# RouteMapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verb", VERBS)
def test_route_mapping_binds_every_supported_verb(verb):
    mapping = RouteMapping()

    getattr(mapping, verb)("/ping", "callback")

    assert mapping.get_routes() == {verb: [{"/ping": "callback"}]}


def test_route_mapping_starts_empty():
    """__routes is a class attribute; each instance must get its own dict."""
    assert RouteMapping().get_routes() == {}


def test_binding_the_same_route_twice_keeps_the_first_callback():
    """
    Silent by design: rebinding is ignored rather than raising. Worth pinning
    because a duplicated path in a controller fails quietly — the second
    callback simply never runs.
    """
    mapping = RouteMapping()

    mapping.get("/ping", "first")
    mapping.get("/ping", "second")

    assert mapping.get_routes()["get"] == [{"/ping": "first"}]


def test_the_same_route_can_be_bound_on_different_verbs():
    mapping = RouteMapping()

    mapping.get("/ping", "reader")
    mapping.post("/ping", "writer")

    assert mapping.get_routes() == {
        "get": [{"/ping": "reader"}],
        "post": [{"/ping": "writer"}],
    }


def test_two_instances_do_not_share_routes():
    first = RouteMapping()
    second = RouteMapping()

    first.get("/ping", "callback")

    assert second.get_routes() == {}


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("end_point", "expected"),
    [
        ("", []),
        ("ping", ["ping"]),
        ("/ping", ["ping"]),
        ("/user/42", ["user", "42"]),
        ("/user/{id}", ["user", "{id}"]),
        ("/a/b/c/", ["a", "b", "c"]),
    ],
)
def test_get_url_params_splits_and_drops_empty_segments(end_point, expected):
    assert Router.get_url_params(end_point) == expected


@pytest.mark.parametrize(
    ("actual", "expected", "matches"),
    [
        ("/ping", "/ping", True),
        ("/user/42", "/user/{id}", True),
        ("/user/42/roles", "/user/{id}", False),  # segment count differs
        ("/user/42", "/group/{id}", False),  # literal segment differs
        ("/a/42/b/7", "/a/{x}/b/{y}", True),
        ("/42", "/{id}", True),
    ],
)
def test_request_matches_route_compares_literals_and_ignores_placeholders(actual, expected, matches):
    router = make_router(make_app(), make_controller(lambda *a, **kw: None))

    assert router.request_matches_route(actual, expected) is matches


def test_get_callback_pattern_names_only_the_placeholders():
    pattern = Router.get_callback_pattern(["user", "{id}", "roles", "{role}"], ["user", "42", "roles", "admin"])

    assert pattern == {"id": "42", "role": "admin"}


def test_get_callback_pattern_is_empty_for_a_literal_route():
    assert Router.get_callback_pattern(["ping"], ["ping"]) == {}


# ---------------------------------------------------------------------------
# Dispatch integration
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verb", VERBS)
def test_dispatch_routes_every_verb_to_its_callback(verb):
    seen = []

    def endpoint(request, app, **params):
        seen.append(request.method)
        return Response({"ok": True})

    app = make_app()
    controller = make_controller(endpoint, method=verb, route="/ping")
    router = make_router(app, controller)

    response = router.dispatch(getattr(RequestFactory(), verb)("/v1/ping"))

    assert response.status_code == 200
    assert seen == [verb.upper()]


def test_url_placeholders_reach_the_callback_as_keyword_arguments():
    received = {}

    def endpoint(request, app, **params):
        received.update(params)
        return Response({"ok": True})

    app = make_app()
    controller = make_controller(endpoint, route="/user/{user_id}/role/{role}")
    router = make_router(app, controller)

    router.dispatch(RequestFactory().get("/v1/user/42/role/admin"))

    assert received == {"user_id": "42", "role": "admin"}


def test_a_verb_that_is_not_mapped_answers_404():
    """The path exists for GET; POSTing to it is not a match, it is a miss."""
    app = make_app()
    controller = make_controller(lambda *a, **kw: Response(None), method="get", route="/ping")
    router = make_router(app, controller)

    response = router.dispatch(RequestFactory().post("/v1/ping"))

    assert response.status_code == 404


def test_options_is_answered_even_when_the_route_is_not_mapped():
    """CORS preflight must succeed without the controller declaring OPTIONS."""
    app = make_app()
    controller = make_controller(lambda *a, **kw: Response(None), method="get", route="/ping")
    router = make_router(app, controller)

    response = router.dispatch(RequestFactory().options("/v1/anything"))

    assert response.status_code == 200


def test_the_root_mount_serves_the_welcome_page():
    """An app mounted at "" answers / with the framework's welcome page."""
    app = make_app("gov_api")
    router = make_router(app, make_controller(lambda *a, **kw: None), route="")

    response = router.dispatch(RequestFactory().get("/"))

    assert response.status_code == 200
    assert b"RINZLER FRAMEWORK" in response.content
    assert b"gov_api" in response.content


def test_every_response_carries_the_default_headers():
    app = make_app()
    controller = make_controller(lambda *a, **kw: Response({"ok": True}))
    router = make_router(app, controller)

    response = router.dispatch(RequestFactory().get("/v1/ping"))

    assert response["access-control-allow-origin"] == "*"
    assert response["access-control-allow-methods"] == app.allowed_methods


# ---------------------------------------------------------------------------
# Edge case worth pinning
# ---------------------------------------------------------------------------


def test_a_uri_shorter_than_the_mount_prefix_raises_index_error():
    """
    `set_end_point_uri` walks the mount's segments and indexes the request's
    segments positionally, so a URI with fewer segments than the mount runs off
    the end of the list. The IndexError is raised before dispatch's try/finally,
    so it escapes as a Django 500 rather than a 404, and the response callback
    never runs.

    Django's URL resolver normally keeps such a request from reaching a Router
    mounted on a longer prefix, which is why this has not surfaced in
    production. Pinned so that guarding the comparison is a deliberate change.
    """
    app = make_app()
    router = make_router(app, make_controller(lambda *a, **kw: None), route="v1/deep")

    with pytest.raises(IndexError):
        router.dispatch(RequestFactory().get("/v1"))
