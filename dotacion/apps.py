from django.apps import AppConfig


class DotacionConfig(AppConfig):
    name = 'dotacion'

    def ready(self):
        import dotacion.receivers  # noqa — registra los receptores