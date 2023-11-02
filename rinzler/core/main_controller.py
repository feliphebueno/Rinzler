from django.views.generic import TemplateView

from rinzler import Rinzler
from rinzler.core.route_mapping import RouteMapping


class MainController(TemplateView):
    """
    Rinzler's default controller for welcome page
    """

    @staticmethod
    def connect(app: Rinzler) -> RouteMapping:
        """
        Maps the end-points to it's route callbacks
        :param app: Rinzler
        :return: RouteMapping
        """
        return app.get_end_point_register()
