from django import template
from django.conf import settings
from django.template import Node
from django.template.loader import render_to_string

from django_q.models import OrmQ, Task
from django_q.tasks import async_task

from rdmo.views.templatetags.view_tags import get_set_value, get_set_values, get_value, get_values

from ..utils import get_adapter, get_group, get_hash, get_project_export

register = template.Library()

adapter = get_adapter()


class LLMNode(Node):

    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render_content(self, context):
        return self.nodelist.render(context)

    def resolve_kwargs(self, context):
        return {k: v.resolve(context) for k, v in self.kwargs.items()}

    @classmethod
    def from_tag(cls, parser, token):
        _, *tag_args = token.split_contents()

        kwargs = {}
        for tag_arg in tag_args:
            if "=" in tag_arg:
                key, value = tag_arg.split("=", 1)
                kwargs[key] = parser.compile_filter(value)

        nodelist = parser.parse(("endllm",))
        parser.delete_first_token()
        return cls(nodelist, kwargs)

    def render(self, context):
        kwargs = self.resolve_kwargs(context)
        prompt = self.render_content(context)

        project = context.get("project")
        view = context.get("view")

        if not project or kwargs.get("verbatim"):
            return f"<pre>{prompt}</pre>"

        project_id = project.id
        snapshot_id = project.snapshot["id"] if project.snapshot else None
        view_id = view["id"]

        task_func = "rdmo_llm_views.tasks.render"
        task_kwargs = {
            "user_prompt": prompt
        }

        task_name = get_hash(project_id, snapshot_id, view_id, **task_kwargs)
        task_group = get_group(project_id, snapshot_id, view_id)

        # check if a task with this name has already be computed
        task = Task.objects.filter(name=task_name).first()

        if task:
            return task.result
        else:
            # check if there is a queued task with that name
            if task_name not in [queued_task.name() for queued_task in OrmQ.objects.all()]:
                async_task(task_func, task_name=task_name, group=task_group, **task_kwargs)

            return render_to_string("llm_views/tags/loading.html", {\
                "project_id": project_id,
                "snapshot_id": snapshot_id,
                "view_id": view_id,
                "timeout": settings.LLM_VIEWS_TIMEOUT
            })


@register.tag()
def llm(parser, token):
    return LLMNode.from_tag(parser, token)


@register.simple_tag(takes_context=True)
def llm_reset(context):
    project = context.get("project")
    view = context.get("view")

    if project:
        project_id = project.id
        snapshot_id = project.snapshot["id"] if project.snapshot else None
        view_id = view["id"]

        return render_to_string("llm_views/tags/reset.html", {
            "project_id": project_id,
            "snapshot_id": snapshot_id,
            "view_id": view_id,
        })
    else:
        return ""


@register.simple_tag(takes_context=True)
def render_project_export(context, project=None):
    if project is None:
        project = context.get("project")
    return get_project_export(project)


@register.simple_tag(takes_context=True)
def format_value(context, attribute, set_prefix="", set_index=0, index=0, project=None):
    value = get_value(context, attribute, set_prefix=set_prefix, set_index=set_index,
                                 index=index, project=project)
    return format_string(value.get("value_and_unit", ""))


@register.simple_tag(takes_context=True)
def format_value_list(context, attribute, set_prefix="", set_index=0, project=None):
    values = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return ", ".join(format_string(value.get("value_and_unit", "")) for value in values)


@register.simple_tag(takes_context=True)
def format_value_inline_list(context, attribute, set_prefix="", set_index=0, project=None):
    values = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return ", ".join(format_string(value.get("value_and_unit", "")) for value in values)


@register.simple_tag(takes_context=True)
def format_set_value(context, set, attribute, set_prefix="", index=0, project=None):
    value = get_set_value(context, set, attribute, set_prefix=set_prefix, index=index, project=project)
    return format_string(value.get("value_and_unit", ""))


@register.simple_tag(takes_context=True)
def format_set_value_list(context, set, attribute, set_prefix="", project=None):
    values = get_set_values(context, set, attribute, set_prefix=set_prefix, project=project)
    return ", ".join(format_string(value.get("value_and_unit", "")) for value in values)


def format_string(string):
    return string.strip().replace("\n", " ").replace("\t", " ")
