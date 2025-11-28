from django import template
from django.conf import settings
from django.template import Node
from django.utils.safestring import mark_safe

from django_q.models import OrmQ, Task
from django_q.tasks import async_task

from ..utils import get_adapter, get_context, get_group, get_hash

register = template.Library()

adapter = get_adapter()


class LLMTemplateNode(Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        template = self.nodelist.render(context)
        resolved = {k: v.resolve(context) for k, v in self.kwargs.items()}

        prompt = resolved.get("prompt")
        attributes = resolved["attributes"].split(",") if resolved.get("attributes") else None

        project = context.get("project")
        view = context.get("view")

        if project:
            context = get_context(project, attributes)

            project_id = project.id
            snapshot_id = project.snapshot["id"] if project.snapshot else None
            view_id = view["id"]

            task_group = get_group(project_id, snapshot_id, view_id)
            task_name = get_hash(project_id, snapshot_id, view_id, prompt, template, context)

            task = Task.objects.filter(name=task_name).first()
            if task:
                return task.result
            else:
                # check if there is a queued task with that name
                if task_name not in [queued_task.name() for queued_task in OrmQ.objects.all()]:
                    async_task(
                        "rdmo_llm_views.tasks.render_tag", prompt, template, context,
                        task_name=task_name, group=task_group
                    )
                return (
                    settings.LLM_VIEWS_PLACEHOLDER +
                    f"<script>setTimeout(() => location.reload(), {settings.LLM_VIEWS_TIMEOUT});</script>"
                )
        else:
            return ""


@register.tag()
def llm(parser, token):
    _, *tag_args = token.split_contents()

    kwargs = {}
    for tag_arg in tag_args:
        if "=" in tag_arg:
            key, value = tag_arg.split("=", 1)
            kwargs[key] = parser.compile_filter(value)

    nodelist = parser.parse(("endllm",))
    parser.delete_first_token()
    return LLMTemplateNode(nodelist, kwargs)


@register.simple_tag(takes_context=True)
def llm_reset(context):
    project = context.get("project")
    view = context.get("view")

    if project:
        project_id = project.id
        snapshot_id = project.snapshot["id"] if project.snapshot else None
        view_id = view["id"]

        return mark_safe(rf"""
            <button id="reset-llm-view" class="btn btn-link">🔄</button>
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
    else:
        return ""
