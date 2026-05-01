from django.conf import settings
from django.core.checks import Error, register

REQUIRED_SETTINGS = [
    ('rdmo_llm_views.E001', 'LLM_VIEWS_ADAPTER', str),
    ('rdmo_llm_views.E002', 'LLM_VIEWS_LLM_ARGS', dict),
    ('rdmo_llm_views.E003', 'LLM_VIEWS_SELECT_MODEL', bool),
    ('rdmo_llm_views.E004', 'LLM_VIEWS_TIMEOUT', int),
    ('rdmo_llm_views.E005', 'Q_CLUSTER', dict),
]


@register()
def check_required_settings(app_configs, **kwargs):
    errors = []
    sentinel = object()  # since None could be a valid value

    for check_id, name, expected_type in REQUIRED_SETTINGS:
        value = getattr(settings, name, sentinel)

        if value is sentinel:
            errors.append(Error(f'settings.{name} is not configured', id=check_id))
            continue

        if not isinstance(value, expected_type):
            errors.append(Error(f'settings.{name} has wrong type: {type(value).__name__}', id=check_id))

    return errors
