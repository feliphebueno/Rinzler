"""
Configuração mínima de Django para a suíte.

O pacote não carrega um projeto Django, mas `Router.dispatch` lê
`settings.DEBUG` e o `RequestFactory` exige settings configurados. Sem isto,
qualquer teste que exercite o router estoura em ImproperlyConfigured.
"""

import django
from django.conf import settings


def pytest_configure():
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            ALLOWED_HOSTS=["*"],
            DEFAULT_CHARSET="utf-8",
            INSTALLED_APPS=[],
            DATABASES={},
            USE_TZ=True,
        )
    django.setup()
