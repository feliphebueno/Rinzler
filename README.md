# Rinzler REST Framework

Django-based REST Micro-Framework

# Install requires

```PHP
pip install rinzler
```

# Usage
```Python

# urls.py

import os
import rinzler

from rinzler.core.main_controller import MainController
from your_controller import Controller

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = rinzler.boot(BASE_DIR)
assembler = app['url_assembler']

urlpatterns = [
    assembler.mount('hello', Controller),
    assembler.mount('', MainController),
]

```

```Python
# your_controller.py
from collections import OrderedDict

from django.http.request import HttpRequest
from django.views.generic import TemplateView

from rinzler.core.response import Response


class Controller(TemplateView):

    def connect(self, app):

        router = app['router']

        # map end-points to callbacks here
        router.get('/world/', self.hello_world)
        router.get('/{name}/', self.hello_user)

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
        try:
            response = OrderedDict()
            response["status"] = True
            response["data"] = "Hello World!"

            return Response(response, content_type="application/json")
        except BaseException as e:
            response = OrderedDict()
            response["status"] = False
            response["mensagem"] = str(e)

            return Response(response, content_type="application/json", status=500)\

    @staticmethod
    def hello_user(request: HttpRequest, app: dict(), **params: dict):
        """
        Default route callback
        :param request HttpRequest
        :param app Rinzler's object
        :param params dict url params, if present
        :rtype: Response
        """
        try:
            user = params['name']
            response = OrderedDict()
            response["status"] = True
            response["data"] = "Hello {0}!".format(user)

            return Response(response, content_type="application/json")
        except BaseException as e:
            response = OrderedDict()
            response["status"] = False
            response["mensagem"] = str(e)

            return Response(response, content_type="application/json", status=500)

```
### Run django
```shell
python manage.py runserver
August 02, 2017 - 18:48:00
Django version 1.10.4, using settings 'Demo.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### Sample requests

```shell
curl http://localhost:8000/
<center><h1>HTTP/1.1 200 OK RINZLER FRAMEWORK</h1></center>

curl http://localhost:8000/hello/world/
{
  "status": true,
  "data": "Hello World!"
}

curl http://localhost:8000/hello/bob/
{
  "status": true,
  "data": "Hello bob!"
}

curl http://localhost:8000/foo/bar/
{
  "status": false,
  "exceptions": {
    "message": "No route found for GET foo/bar/"
  },
  "request": {
    "content": "",
    "method": "GET",
    "path_info": "foo/bar/"
  },
  "message": "We are sorry, but something went terribly wrong."
}

```
