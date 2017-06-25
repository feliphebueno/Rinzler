# Rinzler REST Framework

Django-based REST Framework

# Requires

```PHP
pip install rinzler
```

# Usage
```Python

# urls.py
from your_controller import Controller
from rinzler.core.url_assembler import UrlAssembler

assembler = UrlAssembler()

urlpatterns = [
    assembler.mount('', Controller)
]


# your_controller.py

from django.http.request import HttpRequest
from django.views.generic import TemplateView

from rinzler.core.response import Response

class Controller(TemplateView):

    def connect(self, app):

        router = app['router']

        router.get('/', self.hello_world)
        return app

    # end-point callbacks here:
    @staticmethod
    def hello_world(request: HttpRequest, app: dict(), **params: dict):
        """
        Default route callback
        :param request HttpRequest
        :param app Rinzler's object
        :param params dict url params, if present
        :rtype: Response
        """
        response = {
            "status": True,
            "data": "Hello World!"
        }

        return Response(response, content_type="application/json")
```
