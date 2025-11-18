from django import template
from django.template import Node

from ..utils import get_adapter, get_context

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
            return adapter.on_tag_render(prompt, template, context)
        else:
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
