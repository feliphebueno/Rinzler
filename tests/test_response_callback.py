"""
Coverage for the response callback.

Why this is the suite's first integration test: the callback is how the
OnyxERP services report every response to their logging service — the
ecosystem's audit trail. It is registered through
`app.set_response_callback(...)` and invoked inside a `finally`, so it runs on
both the success and the failure path. If it stops firing, auditing disappears
with no exception and no log entry: a silent failure.
"""

import pytest
from django.test import RequestFactory

from tests.helpers import CallbackSpy, make_app, make_controller, make_router


def status_of(response) -> int:
    """
    Status of the object handed to the callback.

    Since 3.1.3 both rinzler's Response and Django's HttpResponse expose
    `status_code` — dispatch may hand over either, depending on the path.
    See `test_callback_object_exposes_status_code`.
    """
    return response.status_code


# ---------------------------------------------------------------------------
# Registration contract
# ---------------------------------------------------------------------------


def test_set_response_callback_rejects_object_without_call_method():
    """The guard exists so the error does not surface on the first request."""
    app = make_app()

    with pytest.raises(TypeError, match="call method"):
        app.set_response_callback(lambda **kwargs: None)


def test_set_response_callback_accepts_object_with_call_and_returns_self():
    app = make_app()
    spy = CallbackSpy()

    assert app.set_response_callback(spy) is app
    assert app.response_callback is spy


def test_call_response_callback_is_a_no_op_when_none_is_registered():
    """Most projects register no callback; that must not blow up."""
    app = make_app()
    router = make_router(app, make_controller(lambda *a, **kw: None))

    assert router.call_response_callback(response=None) is True


def test_call_response_callback_forwards_its_kwargs():
    app = make_app()
    spy = CallbackSpy()
    app.set_response_callback(spy)
    router = make_router(app, make_controller(lambda *a, **kw: None))

    router.call_response_callback(response="resp", method="GET")

    assert spy.calls == [{"response": "resp", "method": "GET"}]


# ---------------------------------------------------------------------------
# Integration through dispatch
# ---------------------------------------------------------------------------


def test_callback_fires_on_the_success_path():
    from rinzler.core.response import Response

    app = make_app("social_api")
    spy = CallbackSpy()
    app.set_response_callback(spy)

    controller = make_controller(lambda request, app, **params: Response({"ok": True}))
    router = make_router(app, controller)

    router.dispatch(RequestFactory().get("/v1/ping"))

    assert spy.was_called
    (payload,) = spy.calls
    assert payload["method"] == "GET"
    assert payload["route"] == "v1"
    assert payload["url"] == "v1/ping"
    assert payload["url_params_like"] == "/ping"
    assert payload["app_name"] == "social_api"
    assert status_of(payload["response"]) == 200


def test_callback_object_exposes_status_code():
    """
    Contract behind the fix for COR-05, pinned here.

    Dispatch hands the callback rinzler's Response *before* calling
    `render()`. It does not subclass HttpResponse, and up to 3.1.2 the status
    was only reachable through `_Response__kwargs`, a name-mangled attribute.

    A consumer moved from reading that private attribute to
    `response.status_code`, which did not exist. That consumer hands the work to
    a background thread, so the AttributeError killed the thread rather than the
    request: every audited write was silently dropped while the API kept
    answering normally.

    The fix exposed the property on the framework rather than pushing every
    consumer to reach into private state. This test keeps it that way.
    """
    from rinzler.core.response import Response

    app = make_app()
    spy = CallbackSpy()
    app.set_response_callback(spy)

    controller = make_controller(lambda request, app, **params: Response({"ok": True}))
    router = make_router(app, controller)

    router.dispatch(RequestFactory().get("/v1/ping"))

    delivered = spy.calls[0]["response"]
    assert isinstance(delivered, Response)
    assert delivered.status_code == 200


def test_callback_fires_when_the_controller_raises():
    """The callback lives in a `finally`: application errors are audited too."""
    app = make_app()
    spy = CallbackSpy()
    app.set_response_callback(spy)

    def exploding_endpoint(request, app, **params):
        raise ValueError("deliberate failure")

    router = make_router(app, make_controller(exploding_endpoint))

    router.dispatch(RequestFactory().get("/v1/ping"))

    assert spy.was_called
    assert status_of(spy.calls[0]["response"]) == 500


def test_callback_fires_for_an_unmapped_route_inside_the_prefix():
    """A 404 from an unmapped route goes through try/finally and is audited."""
    app = make_app()
    spy = CallbackSpy()
    app.set_response_callback(spy)

    router = make_router(app, make_controller(lambda *a, **kw: None))

    router.dispatch(RequestFactory().get("/v1/no-such-route"))

    assert spy.was_called
    assert status_of(spy.calls[0]["response"]) == 404


def test_callback_does_NOT_fire_when_the_mount_prefix_does_not_match():
    """
    Known gap in the audit trail, pinned here as current behaviour.

    When the URI does not match the prefix the Router was mounted on, dispatch
    returns *before* the try/finally block (see the `if not
    self.set_end_point_uri(uri)` guard in `rinzler/core/router.py`), so the
    callback never runs. The 404 reaches the client while the logging service
    receives nothing. Tracked as COR-06 in the OnyxERP tracker.

    If that is ever fixed, this is the test that should change — and the
    change is intentional, not a regression.
    """
    app = make_app()
    spy = CallbackSpy()
    app.set_response_callback(spy)

    router = make_router(app, make_controller(lambda *a, **kw: None), route="v1")

    response = router.dispatch(RequestFactory().get("/other-prefix/ping"))

    assert response.status_code == 404
    assert not spy.was_called
