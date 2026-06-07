from django.apps import AppConfig


class GbvConfig(AppConfig):
    name = 'apps.gbv'

    def ready(self):
        pass  # signals will go here later