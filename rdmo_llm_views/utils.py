from django.conf import settings

from rdmo.core.utils import import_class
from rdmo.projects.exports import AnswersExportMixin


def get_adapter():
    return import_class(settings.LLM_VIEWS_ADAPTER)()


def get_project(project):
    export_plugin = AnswersExportMixin()
    export_plugin.project = project
    export_plugin.snapshot = None

    data = export_plugin.get_data()
    return data
