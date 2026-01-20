import hashlib
import json
from urllib.parse import urlparse

from django.conf import settings
from django.utils.safestring import mark_safe

from django_q.models import OrmQ, Task
from django_q.tasks import async_task

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


def get_context(project_wrapper, attributes):
    if attributes:
        questions = filter_questions(project_wrapper._project.catalog.questions, attributes)
        answer_tree = project_wrapper._project.get_answer_tree(verbose=(
            "page", "questionset", "question", "value"
        ))
        return filter_elements(answer_tree, [q.uri for q in questions])
    else:
        return get_project(project_wrapper._project)


def get_project(project):
    export_plugin = AnswersExportMixin()
    export_plugin.project = project
    export_plugin.snapshot = None

    data = export_plugin.get_data()
    return data


def filter_questions(questions, attributes):
    filtered_questions = []
    for attribute in attributes:
        if urlparse(attribute).scheme:
            filtered_questions += list(filter(lambda q: q.attribute and (q.attribute.uri == attribute), questions))
        else:
            filtered_questions += list(filter(lambda q: q.attribute and (q.attribute.path == attribute), questions))
    return filtered_questions


def filter_elements(element_node, uris):
    model = element_node.get("model")

    if model == "questions.catalog":
        return [
            page
            for element in element_node.get("elements", [])
            for page in filter_elements(element, uris)
        ]
    if model == "questions.section":
        return [
            filtered_element for filtered_element in [
                filter_elements(element, uris)
                for element in element_node.get("elements", [])
            ] if filtered_element
        ]
    elif model in ["questions.page", "questions.questionset"]:
        filtered_sets = [
            filtered_set for filtered_set in [
                filter_elements(set_element, uris)
                for set_node in element_node.get("sets", [])
                for set_element in set_node.get("elements", [])
            ] if filtered_set
        ]

        if filtered_sets:
            return {
                "title": element_node.get("title"),
                "sets": filtered_sets
            }
        else:
            return None
    else:
        uri = element_node.get("uri")
        if uri in uris:
            return {
                "question": element_node.get("text"),
                "answers": [
                    value.get("value_and_unit") for value in element_node.get("values", []) if not value.get("is_empty")
                ]
            }
        else:
            return None


def render_tag_async(task_func, task_name, task_group, **task_kwargs):
    task = Task.objects.filter(name=task_name).first()
    if task:
        return task.result
    else:
        # check if there is a queued task with that name
        if task_name not in [queued_task.name() for queued_task in OrmQ.objects.all()]:
            async_task(task_func, task_name=task_name, group=task_group, **task_kwargs)
        return (
            settings.LLM_VIEWS_PLACEHOLDER +
            f"<script>setTimeout(() => location.reload(), {settings.LLM_VIEWS_TIMEOUT});</script>"
        )


def render_reset_button(project_id, snapshot_id, view_id):
    return mark_safe(rf"""
        {settings.LLM_VIEWS_RESET_BUTTON}
        <script>
            const button = document.getElementById('reset-llm-view')
            const handleClick = () => {{
                const baseUrl = document.querySelector('meta[name="baseurl"]').content.replace(/\/+$/, '')
                const url = `${{baseUrl}}/api/v1/llm-views/projects/{project_id}/reset/`

                fetch(url, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }},
                    body: JSON.stringify({{
                        snapshot: {snapshot_id or 'null'},
                        view: {view_id}
                    }})
                }}).then(() => location.reload())
            }}

            button.addEventListener('click', handleClick);
        </script>
    """)
