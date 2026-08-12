"""
Cobertura da Response — em especial do `status_code`.

A propriedade existe porque a Response é entregue ao response callback
**antes** de `render()`, e até então o status só existia em `_Response__kwargs`.
Ler atributo com name mangling de fora do pacote foi o que produziu o COR-05:
o `ResponseCallbackService` do onyxerp 3.x assumiu `response.status_code`,
que não existia, e derrubava a requisição inteira dentro de um `finally`.
"""

import pytest

from rinzler.core.response import Response


def test_status_code_default_e_200():
    """Sem status explícito, o mesmo default do HttpResponse."""
    assert Response({"ok": True}).status_code == 200


@pytest.mark.parametrize("status", [200, 201, 204, 400, 401, 403, 404, 409, 413, 500])
def test_status_code_reflete_o_status_informado(status):
    assert Response(None, status=status).status_code == status


def test_status_code_e_o_mesmo_que_o_render_produz():
    """
    O invariante que de fato importa: o valor lido antes do render tem de ser
    o valor que o cliente recebe. Se os dois divergirem, a auditoria registra
    um status diferente do que foi respondido.
    """
    for status in (200, 404, 500):
        resposta = Response({"x": 1}, status=status)
        assert resposta.status_code == resposta.render().status_code


def test_status_code_e_somente_leitura():
    """Escrever aqui não teria efeito no render; melhor falhar alto."""
    with pytest.raises(AttributeError):
        Response(None, status=200).status_code = 500


def test_render_continua_funcionando_normalmente():
    """A propriedade não pode ter alterado o comportamento existente."""
    renderizada = Response({"ok": True}, status=201).render()

    assert renderizada.status_code == 201
    assert renderizada.content == b'{"ok": true}'
