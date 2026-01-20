from django import template
from django.template import Node

from ..utils import get_adapter, get_context, get_group, get_hash, render_reset_button, render_tag_async

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
        tag_name = token.contents.split()[0]

        _, *tag_args = token.split_contents()

        kwargs = {}
        for tag_arg in tag_args:
            if "=" in tag_arg:
                key, value = tag_arg.split("=", 1)
                kwargs[key] = parser.compile_filter(value)

        nodelist = parser.parse((f"end_{tag_name}",))
        parser.delete_first_token()
        return cls(nodelist, kwargs)


class LLMTemplateNode(LLMNode):

    def render(self, context):
        project = context.get("project")
        view = context.get("view")

        if project:
            template = self.render_content(context)
            kwargs = self.resolve_kwargs(context)

            prompt = kwargs.get("prompt")
            attributes = kwargs.get("attributes").split(",") if kwargs.get("attributes") else None

            context = get_context(project, attributes)

            project_id = project.id
            snapshot_id = project.snapshot["id"] if project.snapshot else None
            view_id = view["id"]

            task = "rdmo_llm_views.tasks.render_template"
            task_kwargs = {
                "context": context,
                "template": template,
                "prompt": prompt
            }

            task_name = get_hash(project_id, snapshot_id, view_id, **task_kwargs)
            task_group = get_group(project_id, snapshot_id, view_id)

            return render_tag_async(task, task_name, task_group, **task_kwargs)

        return ""


class LLMPromptNode(LLMNode):

    def render(self, context):
        project = context.get("project")
        view = context.get("view")

        if project:
            user_prompt = self.render_content(context)

            project = context.get("project")
            view = context.get("view")

            project_id = project.id
            snapshot_id = project.snapshot["id"] if project.snapshot else None
            view_id = view["id"]

            task = "rdmo_llm_views.tasks.render_prompt"
            task_kwargs = {
                "user_prompt": user_prompt
            }

            task_name = get_hash(project_id, snapshot_id, view_id, **task_kwargs)
            task_group = get_group(project_id, snapshot_id, view_id)

            return render_tag_async(task, task_name, task_group, **task_kwargs)

        return ""


@register.tag()
def llm_template(parser, token):
    return LLMTemplateNode.from_tag(parser, token)


@register.tag()
def llm_prompt(parser, token):
    return LLMPromptNode.from_tag(parser, token)


@register.simple_tag(takes_context=True)
def llm_reset(context):
    project = context.get("project")
    view = context.get("view")

    if project:
        project_id = project.id
        snapshot_id = project.snapshot["id"] if project.snapshot else None
        view_id = view["id"]

        return render_reset_button(project_id, snapshot_id, view_id)

    return ""
