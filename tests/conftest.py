"""
Minimal Django configuration for the test suite.

The package does not ship a Django project, but `Router.dispatch` reads
`settings.DEBUG` and `RequestFactory` requires configured settings. Without
this, any test exercising the router blows up with ImproperlyConfigured.
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
