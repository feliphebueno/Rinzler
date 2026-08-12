"""
Cobertura do response callback.

Por que este é o primeiro teste de integração da suíte: o callback é o
mecanismo por onde os serviços do OnyxERP reportam toda resposta à LogAPI —
a trilha de auditoria do ecossistema. Ele é montado por
`app.set_response_callback(...)` e invocado num `finally`, ou seja, no caminho
de sucesso e no de erro. Se parar de disparar, a auditoria some sem lançar
exceção e sem log: falha silenciosa.
"""

from unittest import mock

import pytest
from django.test import RequestFactory

from rinzler import Rinzler
from rinzler.core.router import Router


class CallbackEspiao:
    """Dublê no formato que `set_response_callback` exige: um objeto com `call`."""

    def __init__(self):
        self.chamadas = []

    def call(self, **kwargs):
        self.chamadas.append(kwargs)

    @property
    def chamou(self) -> bool:
        return len(self.chamadas) > 0


def cria_app(nome="test") -> Rinzler:
    """App com log silenciado e sem serviço de autenticação."""
    with mock.patch.object(Rinzler, "set_log"):
        app = Rinzler(nome)
    app.log = mock.Mock()
    # O Router lê `app.auth_service` no __init__; a classe só tem a anotação.
    app.auth_service = None
    return app


def cria_controller(callback, metodo="get", rota="/ping"):
    """Controller no contrato do rinzler: chamável que expõe `connect(app)`."""

    class Controller:
        def connect(self, app):
            rotas = app.get_end_point_register()
            getattr(rotas, metodo)(rota, callback)
            return rotas

    return Controller


def cria_router(app, controller, route="v1") -> Router:
    return Router(app=app, route=route, controller=controller)


def status_de(response) -> int:
    """
    Status do objeto entregue ao callback.

    Desde a 3.1.3 tanto a `Response` do rinzler quanto o `HttpResponse` do
    Django expõem `status_code` — o `dispatch` pode entregar qualquer um dos
    dois, dependendo do caminho. Ver `test_o_objeto_do_callback_expoe_status_code`.
    """
    return response.status_code


# ---------------------------------------------------------------------------
# Contrato de registro
# ---------------------------------------------------------------------------


def test_set_response_callback_recusa_objeto_sem_metodo_call():
    """A guarda existe para o erro não aparecer só na primeira requisição."""
    app = cria_app()

    with pytest.raises(TypeError, match="call method"):
        app.set_response_callback(lambda **kwargs: None)


def test_set_response_callback_aceita_objeto_com_call_e_retorna_self():
    app = cria_app()
    espiao = CallbackEspiao()

    assert app.set_response_callback(espiao) is app
    assert app.response_callback is espiao


def test_call_response_callback_e_no_op_sem_callback_configurado():
    """A maioria dos projetos não registra callback; isso não pode explodir."""
    app = cria_app()
    router = cria_router(app, cria_controller(lambda *a, **kw: None))

    assert router.call_response_callback(response=None) is True


def test_call_response_callback_encaminha_os_kwargs():
    app = cria_app()
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)
    router = cria_router(app, cria_controller(lambda *a, **kw: None))

    router.call_response_callback(response="resp", method="GET")

    assert espiao.chamadas == [{"response": "resp", "method": "GET"}]


# ---------------------------------------------------------------------------
# Integração pelo dispatch
# ---------------------------------------------------------------------------


def test_callback_dispara_no_caminho_de_sucesso():
    from rinzler.core.response import Response

    app = cria_app("social_api")
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)

    controller = cria_controller(lambda request, app, **params: Response({"ok": True}))
    router = cria_router(app, controller)

    router.dispatch(RequestFactory().get("/v1/ping"))

    assert espiao.chamou
    (payload,) = espiao.chamadas
    assert payload["method"] == "GET"
    assert payload["route"] == "v1"
    assert payload["url"] == "v1/ping"
    assert payload["url_params_like"] == "/ping"
    assert payload["app_name"] == "social_api"
    assert status_de(payload["response"]) == 200


def test_o_objeto_do_callback_expoe_status_code():
    """
    Correção do COR-05, fixada como contrato.

    O `dispatch` entrega ao callback a `Response` do rinzler **antes** de
    chamar `render()`. Ela não herda de `HttpResponse`, e até a 3.1.2 o status
    só era alcançável por `_Response__kwargs` — atributo com name mangling.

    O `ResponseCallbackService` do onyxerp lia assim na linha 2.x e passou, na
    3.x, a fazer `response.status_code`. Como o callback roda dentro do
    `finally` do `dispatch` e não há `try/except` no caminho, o AttributeError
    escapava e derrubava **toda** requisição.

    A correção foi expor a propriedade no framework, em vez de obrigar cada
    consumidor a alcançar estado privado. Este teste garante que o objeto
    entregue ao callback continua respondendo a `status_code`.
    """
    from rinzler.core.response import Response

    app = cria_app()
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)

    controller = cria_controller(lambda request, app, **params: Response({"ok": True}))
    router = cria_router(app, controller)

    router.dispatch(RequestFactory().get("/v1/ping"))

    entregue = espiao.chamadas[0]["response"]
    assert isinstance(entregue, Response)
    assert entregue.status_code == 200


def test_callback_dispara_quando_o_controller_lanca_excecao():
    """O callback vive num `finally`: erro de aplicação também é auditado."""
    app = cria_app()
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)

    def callback_que_explode(request, app, **params):
        raise ValueError("falha proposital")

    router = cria_router(app, cria_controller(callback_que_explode))

    router.dispatch(RequestFactory().get("/v1/ping"))

    assert espiao.chamou
    assert status_de(espiao.chamadas[0]["response"]) == 500


def test_callback_dispara_quando_a_rota_nao_existe_dentro_do_prefixo():
    """404 de rota não mapeada passa pelo try/finally e é auditado."""
    app = cria_app()
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)

    router = cria_router(app, cria_controller(lambda *a, **kw: None))

    router.dispatch(RequestFactory().get("/v1/rota-que-nao-existe"))

    assert espiao.chamou
    assert status_de(espiao.chamadas[0]["response"]) == 404


def test_callback_NAO_dispara_quando_o_prefixo_do_mount_nao_casa():
    """
    Lacuna conhecida da trilha de auditoria, fixada aqui como comportamento.

    Quando a URI não bate com o prefixo em que o Router foi montado, o
    `dispatch` retorna **antes** do bloco try/finally
    (`rinzler/core/router.py`, o `if not self.set_end_point_uri(uri)`), e o
    callback nunca é chamado. A resposta 404 sai para o cliente sem que a
    LogAPI receba registro nenhum.

    Se um dia isso for corrigido, é este teste que deve mudar — e a mudança
    é intencional, não regressão.
    """
    app = cria_app()
    espiao = CallbackEspiao()
    app.set_response_callback(espiao)

    router = cria_router(app, cria_controller(lambda *a, **kw: None), route="v1")

    resposta = router.dispatch(RequestFactory().get("/outro-prefixo/ping"))

    assert resposta.status_code == 404
    assert not espiao.chamou
