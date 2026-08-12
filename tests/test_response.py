"""
Coverage for Response, and for `status_code` in particular.

The property exists because Response is handed to the response callback
*before* `render()` is called, and until then the status only lived in
`_Response__kwargs`. Reading a name-mangled attribute from outside the package
is what caused the defect tracked as COR-05 in the OnyxERP tracker: a consumer
assumed `response.status_code`, which did not exist, and the resulting
AttributeError escaped a `finally` block and took down every request.
"""

import pytest

from rinzler.core.response import Response


def test_status_code_defaults_to_200():
    """No explicit status means 200, same default as HttpResponse."""
    assert Response({"ok": True}).status_code == 200


@pytest.mark.parametrize("status", [200, 201, 204, 400, 401, 403, 404, 409, 413, 500])
def test_status_code_reflects_the_given_status(status):
    assert Response(None, status=status).status_code == status


def test_status_code_matches_what_render_produces():
    """
    The invariant that actually matters: the value read before render must be
    the value the client receives. If they diverge, an audit trail records a
    status different from the one that was answered.
    """
    for status in (200, 404, 500):
        response = Response({"x": 1}, status=status)
        assert response.status_code == response.render().status_code


def test_status_code_is_read_only():
    """Assigning here would not affect render, so fail loudly instead."""
    with pytest.raises(AttributeError):
        Response(None, status=200).status_code = 500


def test_render_still_behaves_as_before():
    """The property must not have changed existing behaviour."""
    rendered = Response({"ok": True}, status=201).render()

    assert rendered.status_code == 201
    assert rendered.content == b'{"ok": true}'
