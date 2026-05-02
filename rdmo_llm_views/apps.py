from django.apps import AppConfig


class LlmViewsConfig(AppConfig):
    name = 'rdmo_llm_views'

    def ready(self):
        from . import checks  # noqa: F401
