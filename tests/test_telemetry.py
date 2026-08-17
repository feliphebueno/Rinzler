"""
Coverage for the only telemetry Rinzler emits.

Rinzler catches every exception and answers with an HTTP status, so the
exception never reaches Django. Automatic instrumentation therefore sees a
plain 5xx response and records no exception: the span says that something
failed, not what. `record_exception_on_span` closes that gap, and these tests
are what keep it closed.

Two properties matter more than the happy path:

- the hook must run in **all five** except branches, because a controller can
  fail through any of them;
- it must **never raise**. It runs inside `except` blocks, where a second
  exception turns a handled 500 into a dead worker.

The tests never touch the global tracer provider — they start a recording span
in the current context, which is the state the function actually reads.
"""

from unittest import mock

import pytest
from django.core.exceptions import RequestDataTooBig
from django.test import RequestFactory
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from rinzler.core import router as router_module
from rinzler.exceptions.auth_exception import AuthException
from rinzler.exceptions.conflict_exception import ConflictException
from rinzler.exceptions.not_found_exception import NotFoundException
from tests.helpers import make_router_raising


def dispatch_in_span(router):
    """
    Dispatch inside a recording span and return the response and the span.

    A local TracerProvider keeps the global one untouched, so test order never
    matters and nothing leaks into the rest of the suite.
    """
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    with provider.get_tracer("tests").start_as_current_span("request"):
        response = router.dispatch(RequestFactory().get("/v1/ping"))

    return response, exporter.get_finished_spans()[0]


def exception_events(span):
    return [event for event in span.events if event.name == "exception"]


# One case per except branch in `Router.dispatch`, in source order. A branch
# missing from this list is a branch where a failure would reach the tracing
# backend as an anonymous 5xx.
#
# The expected `exception.type` is written out fully because that is what the
# backend actually shows: OpenTelemetry qualifies the name with its module for
# everything outside `builtins`, which is why ValueError is the odd one out.
BRANCHES = [
    (NotFoundException("gone"), 404, "rinzler.exceptions.not_found_exception.NotFoundException"),
    (AuthException("nope"), 403, "rinzler.exceptions.auth_exception.AuthException"),
    (ConflictException("clash"), 409, "rinzler.exceptions.conflict_exception.ConflictException"),
    (RequestDataTooBig(), 413, "django.core.exceptions.RequestDataTooBig"),
    (ValueError("anything unmapped"), 500, "ValueError"),
]
IDS = ["not_found", "auth", "rinzler_http", "request_too_big", "unmapped"]


@pytest.mark.parametrize(("exception", "status", "type_name"), BRANCHES, ids=IDS)
def test_every_except_branch_attaches_the_exception(exception, status, type_name):
    response, span = dispatch_in_span(make_router_raising(exception))

    assert response.status_code == status
    events = exception_events(span)
    assert len(events) == 1
    assert events[0].attributes["exception.type"] == type_name


@pytest.mark.parametrize(("exception", "status", "type_name"), BRANCHES, ids=IDS)
def test_every_except_branch_marks_the_span_as_error(exception, status, type_name):
    _, span = dispatch_in_span(make_router_raising(exception))

    assert span.status.status_code is StatusCode.ERROR


def test_the_stack_trace_travels_with_the_span():
    """Without this the span names the failure but cannot locate it."""
    _, span = dispatch_in_span(make_router_raising(ValueError("boom")))

    assert "boom" in exception_events(span)[0].attributes["exception.stacktrace"]


def test_a_successful_request_records_nothing():
    """Telemetry on the error path only — a 200 must stay clean."""

    from rinzler.core.response import Response
    from tests.helpers import make_app, make_controller, make_router

    def endpoint(request, app, **params):
        return Response({"ok": True})

    router = make_router(make_app(), make_controller(endpoint))
    _, span = dispatch_in_span(router)

    assert exception_events(span) == []
    assert span.status.status_code is not StatusCode.ERROR


# ---------------------------------------------------------------------------
# It must never raise
# ---------------------------------------------------------------------------


def test_a_failure_inside_the_hook_does_not_break_the_response():
    """
    The regression this whole release hangs on: the hook runs inside `except`
    blocks, so an exception raised here would escape dispatch and kill the
    worker — turning a handled 404 into a crash.
    """
    with mock.patch.object(router_module._otel_trace, "get_current_span", side_effect=RuntimeError("otel is down")):
        response = make_router_raising(NotFoundException("gone")).dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 404


def test_a_failure_inside_record_exception_does_not_break_the_response():
    """Same guarantee one layer deeper: the exporter itself misbehaving."""
    broken = mock.Mock()
    broken.is_recording.return_value = True
    broken.record_exception.side_effect = RuntimeError("exporter is down")

    with mock.patch.object(router_module._otel_trace, "get_current_span", return_value=broken):
        response = make_router_raising(ValueError("boom")).dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# No SDK, and no OpenTelemetry at all
# ---------------------------------------------------------------------------


def test_without_an_sdk_the_hook_is_a_no_op():
    """
    The state of every service that wants no telemetry: the API is installed,
    no provider is configured, the current span is non-recording. Dispatch has
    to behave exactly as it did before this feature existed.
    """
    response = make_router_raising(NotFoundException("gone")).dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 404


def test_without_opentelemetry_installed_dispatch_still_works():
    """
    `opentelemetry-api` is declared in setup.py, so this should not happen —
    but a library that dies when an optional-looking import is missing is a
    library that takes nine services down with it.
    """
    with mock.patch.object(router_module, "_otel_trace", None):
        response = make_router_raising(ValueError("boom")).dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 500
