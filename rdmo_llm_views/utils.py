import hashlib
import json

from django.conf import settings

from rdmo.core.utils import import_class
from rdmo.projects.exports import AnswersExportMixin


def get_adapter():
    return import_class(settings.LLM_VIEWS_ADAPTER)()


def get_group(*args, **kwargs):
    values = ["" if x is None else str(x) for x in (*args, *kwargs.values())]
    return ":".join(values)


def get_hash(*args, **kwargs):
    values = ["" if x is None else str(x) for x in (*args, *kwargs.values())]
    raw = json.dumps(values)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_project_export(project_wrapper):
    if project_wrapper:
        data = [
            {
                "question": "What is the title of the project?",
                "set": "",
                "values": project_wrapper.title
            },
            {
                "question": "What is the description of the project?",
                "set": "",
                "values": project_wrapper.description
            },
        ]

        export_plugin = AnswersExportMixin()
        export_plugin.project = project_wrapper._project
        export_plugin.snapshot = None

        data += export_plugin.get_data()
        return json.dumps(data, indent=2).replace(r"{", r"{{").replace(r"}", r"}}")
    else:
        return []
