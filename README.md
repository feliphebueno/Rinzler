# Rinzler REST Framework

Django-based REST Micro-Framework

# Install requires

```bash
pip install rinzler
```

# Usage
```Python
# urls.py
from rinzler import boot, Rinzler

from rinzler.core.main_controller import MainController
from your_controller import Controller


app: Rinzler = boot("MyApp")

urlpatterns = [
    app.mount('hello', Controller),
    app.mount('', MainController),
]
```

```Python
# your_controller.py
from django.http.request import HttpRequest

from rinzler import Rinzler
from rinzler.core.response import Response


class Controller:

    def connect(self, app):

        router = app.get_end_point_register()

        # map end-points to callbacks here
        router.get('/world/', self.hello_world)
        router.get('/{name}/', self.hello_user)

        return router

    # end-point callbacks here:
    @staticmethod
    def hello_world(request: HttpRequest, app: Rinzler, **params: dict):
        """
        Default route callback
        :param request HttpRequest
        :param app Rinzler's object
        :param params dict url params, if present
        :rtype: Response
        """
        try:
            response = {
                "status": True,
                "data": "Hello World!",
            }
            return Response(response, content_type="application/json")
        except BaseException as e:
            response = {
                "status": False,
                "mensagem": str(e),
            }
            return Response(response, content_type="application/json", status=500)\

    @staticmethod
    def hello_user(request: HttpRequest, app: Rinzler, **params: dict) -> Response:
        try:
            user = params['name']
            response = {
                "status": True,
                "data": f"Hello {user}!",
            }

            return Response(response, content_type="application/json")
        except BaseException as e:
            response = {
                "status": False,
                "mensagem": str(e),
            }
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
# If project's settings has DEBUG=True, otherwise: empty response body with status-code 404
```


### Authentication
Authentication can be done on a per-route basis thus allowing to have authenticated and non-authenticated routes on the application.

To do so, first you need to create a class that inherits from `BaseAuthService` and implements the `authenticate` method.

```Python
from django.http.request import HttpRequest

from rinzler.auth.base_auth_service import BaseAuthService

class MyAuthenticationService(BaseAuthService):
    def authenticate(self, request: HttpRequest, auth_route: str, params: dict) -> bool:
        """
        Implement your authentication logic here
        :param request: HttpRequest Django's request object
        :param auth_route: str route being requested
        :param params: dict url params, if present
        :return: bool if not True, the request will be promptly returned with status-code 403
        """
        # Non-authenticated route
        if auth_route == 'GET_v1/hello/world/':
            return True

        # Authenticated routes
        if request.META.get("HTTP_AUTHORIZATION"):
            # after performing your authentication logic, you can append user data to the Rinzler object so it'll be available on the controller
            self.auth_data = {
                "user_id": 1,
            }
            return True
```

Then, you need to register your authentication service on the application's `urls.py` file.

```Python
# urls.py
from rinzler import boot, Rinzler

from rinzler.core.main_controller import MainController
from your_controller import Controller
from my_auth_service import MyAuthenticationService


app: Rinzler = boot("MyApp")
app.set_auth_service(MyAuthenticationService())

urlpatterns = [
    app.mount('hello', Controller),
    app.mount('', MainController),
]
```
    
Finally, you can access the user data on the controller by accessing the `auth_data` attribute on the Rinzler object.
```Python
# your_controller.py
from django.http.request import HttpRequest

from rinzler import Rinzler
from rinzler.core.response import Response


class Controller:
    # ...
    @staticmethod
    def hello_user(request: HttpRequest, app: Rinzler, **params: dict) -> Response:
        try:
            user = params['name']
            user_id = app.auth_data['user_id']
            response = {
                "status": True,
                "data": f"Hello {user}! Your user id is {user_id}.",
            }

            return Response(response, content_type="application/json")
        except BaseException as e:
            response = {
                "status": False,
                "mensagem": str(e),
            }
            return Response(response, content_type="application/json", status=500)
```
### Sample requests

```shell
# Non-authenticated request
curl http://localhost:8000/hello/world/
{
  "status": true,
  "data": "Hello World!"
}

# Improperly authenticated request
curl http://localhost:8000/hello/bob/
# (empty response body with status-code 403)

# Properly authenticated request
curl http://localhost:8000/hello/bob/ -H "Authorization: XYZ"
{
  "status": true,
  "data": "Hello bob! Your user id is 1"
}
```
