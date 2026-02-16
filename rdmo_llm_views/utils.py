import hashlib
import json

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
