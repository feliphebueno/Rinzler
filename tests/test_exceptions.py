"""
Coverage for the exception-to-HTTP-status mapping.

The framework's whole error-handling contract is this: a controller raises one
of the RinzlerHttpException subclasses, and dispatch turns it into a response
carrying the matching status. Nothing verified that mapping before, even though
every service in the ecosystem depends on it to answer 404, 403 and 400.

Order matters in dispatch's except chain — NotFoundException and AuthException
are caught ahead of the generic RinzlerHttpException, and both are subclasses
of it. Exercising all sixteen through dispatch is what proves the chain is
still wired correctly.
"""

import pytest
from django.core.exceptions import RequestDataTooBig
from django.test import RequestFactory

from rinzler.exceptions import RinzlerHttpException
from rinzler.exceptions.auth_exception import AuthException
from rinzler.exceptions.conflict_exception import ConflictException
from rinzler.exceptions.content_too_large_exception import ContentTooLargeException
from rinzler.exceptions.expectation_failed_exception import ExpectationFailedException
from rinzler.exceptions.failed_dependency_exception import FailedDependencyException
from rinzler.exceptions.gone_exception import GoneException
from rinzler.exceptions.i_am_a_teapot_exception import IMaTeapotException
from rinzler.exceptions.internal_exception import InternalException
from rinzler.exceptions.invalid_input_exception import InvalidInputException
from rinzler.exceptions.not_allowed_exception import NotAllowedException
from rinzler.exceptions.not_found_exception import NotFoundException
from rinzler.exceptions.precondition_failed_exception import PreconditionFailedException
from rinzler.exceptions.precondition_required_exception import PreconditionRequiredException
from rinzler.exceptions.service_unavailable_exception import ServiceUnavailableException
from rinzler.exceptions.unacceptable_input_exception import UnacceptableInputException
from rinzler.exceptions.unauthorized_exception import UnauthorizedException
from tests.helpers import make_router_raising

# The mapping, written out on purpose. A generated table would pass even if
# every status were wrong; this one states what the framework promises.
EXCEPTIONS = [
    (InvalidInputException, 400, "Bad Request"),
    (UnauthorizedException, 401, "Unauthorized"),
    (AuthException, 403, "Forbidden"),
    (NotFoundException, 404, "Not Found"),
    (NotAllowedException, 405, "Method Not Allowed"),
    (UnacceptableInputException, 406, "Not Acceptable"),
    (ConflictException, 409, "Conflict"),
    (GoneException, 410, "Gone"),
    (PreconditionFailedException, 412, "Precondition Failed"),
    (ContentTooLargeException, 413, "Payload Too Large"),
    (ExpectationFailedException, 417, "Expectation Failed"),
    (IMaTeapotException, 418, "I'm a teapot"),
    (FailedDependencyException, 424, "Failed Dependency"),
    (PreconditionRequiredException, 428, "Precondition Required"),
    (InternalException, 500, "Internal Server Error"),
    (ServiceUnavailableException, 503, "Service Unavailable"),
]

IDS = [exc.__name__ for exc, _, _ in EXCEPTIONS]


def test_all_sixteen_exceptions_are_covered():
    """A new exception without a row here is an untested status mapping."""
    import pathlib

    import rinzler.exceptions

    modules = pathlib.Path(rinzler.exceptions.__file__).parent.glob("*_exception.py")

    assert sorted(m.stem for m in modules) == sorted(
        exc.__module__.rsplit(".", 1)[-1] for exc, _, _ in EXCEPTIONS
    )


@pytest.mark.parametrize(("exception", "status", "name"), EXCEPTIONS, ids=IDS)
def test_exception_declares_its_status_and_name(exception, status, name):
    assert exception.status_code == status
    assert exception.exception_name == name


@pytest.mark.parametrize(("exception", "status", "name"), EXCEPTIONS, ids=IDS)
def test_exception_status_is_a_valid_http_code(exception, status, name):
    """
    Django refuses to render anything outside 100..599, and the refusal
    surfaces from inside dispatch's `finally` — see
    `test_base_exception_status_zero_breaks_rendering`.
    """
    assert 100 <= exception.status_code <= 599


@pytest.mark.parametrize(("exception", "status", "name"), EXCEPTIONS, ids=IDS)
def test_exception_converts_to_its_status_code(exception, status, name):
    """RinzlerHttpException defines __int__, so int(exc) is the status."""
    assert int(exception()) == status


@pytest.mark.parametrize(("exception", "status", "name"), EXCEPTIONS, ids=IDS)
def test_dispatch_converts_the_exception_into_its_http_status(exception, status, name):
    """The contract that matters: raised in a controller, answered as status."""
    router = make_router_raising(exception("raised by test"))

    response = router.dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == status


def test_every_status_code_is_distinct():
    """Two exceptions sharing a status would make the mapping ambiguous."""
    codes = [exc.status_code for exc, _, _ in EXCEPTIONS]

    assert len(set(codes)) == len(codes)


# ---------------------------------------------------------------------------
# Paths handled ahead of the generic branch
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    ["JWT não informado.", "Token inválido ou expirado.", "any other message"],
)
def test_auth_exception_answers_403_regardless_of_its_message(message):
    """
    Dispatch special-cases two AuthException messages to log them at info
    instead of exception. That changes the log level only — the answer must
    stay 403 in every case.
    """
    router = make_router_raising(AuthException(message))

    response = router.dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 403


def test_request_data_too_big_answers_413():
    """Django's own exception reaches the same status as ContentTooLargeException."""
    router = make_router_raising(RequestDataTooBig())

    response = router.dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 413


def test_unknown_exception_answers_500():
    """Anything not in the hierarchy is an internal error, not a leak."""
    router = make_router_raising(ValueError("something the framework knows nothing about"))

    response = router.dispatch(RequestFactory().get("/v1/ping"))

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Edge case worth pinning
# ---------------------------------------------------------------------------


def test_base_exception_status_zero_breaks_rendering():
    """
    RinzlerHttpException carries `status_code = 0`, and its docstring says
    subclasses must override it. Raising the base class directly is therefore
    misuse — but the failure mode is worth knowing: dispatch catches it, builds
    `Response(None, status=0)`, and rendering that inside the `finally` raises
    ValueError, which escapes dispatch entirely. The client gets a Django
    traceback instead of any HTTP error, and the response callback has already
    run with a response that can never be rendered.

    Pinned so that giving the base class a sane default is a deliberate change,
    not an accident.
    """
    assert RinzlerHttpException.status_code == 0

    router = make_router_raising(RinzlerHttpException("raised by test"))

    with pytest.raises(ValueError, match="status code must be an integer"):
        router.dispatch(RequestFactory().get("/v1/ping"))
