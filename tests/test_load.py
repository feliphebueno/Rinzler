from unittest import TestCase, mock

from django.urls import URLPattern
from django.views.generic import TemplateView

from rinzler import Rinzler


class RinzlerTest(TestCase):
    def setUp(self) -> None:
        Rinzler.set_log = mock.Mock()
        self.app = Rinzler("test")

    def test_mount(self):
        class DummyController(TemplateView):
            pass

        self.assertIsInstance(self.app.mount("/", DummyController), URLPattern)
