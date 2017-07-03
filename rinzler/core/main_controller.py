"""
Rinzler's default controller for welcome page
"""

from django.views.generic import TemplateView


class MainController(TemplateView):

    @staticmethod
    def connect(app):
        return app
