from django import template
from django.conf import settings
from django.template import Node

from django_q.models import Task
from django_q.tasks import async_task

from ..utils import get_adapter, get_context, get_hash

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

        project_wrapper = context.get("project")

        if project_wrapper:
            context = get_context(project_wrapper, attributes)
            task_name = f'project="{project_wrapper.title}" hash={get_hash(prompt, template, context)}'

            task = Task.objects.filter(name=task_name).first()
            if task:
                return task.result
            else:
                async_task("rdmo_llm_views.tasks.render_tag", prompt, template, context, task_name=task_name)
                return (
                    settings.LLM_VIEWS_PLACEHOLDER +
                    f"<script>setTimeout(() => location.reload(), {settings.LLM_VIEWS_TIMEOUT});</script>"
                )

        return ""


@register.tag(name="llm")
def llm_template(parser, token):
    _, *tag_args = token.split_contents()

    kwargs = {}
    for tag_arg in tag_args:
        if "=" in tag_arg:
            key, value = tag_arg.split("=", 1)
            kwargs[key] = parser.compile_filter(value)

    nodelist = parser.parse(("endllm",))
    parser.delete_first_token()
    return LLMTemplateNode(nodelist, kwargs)
