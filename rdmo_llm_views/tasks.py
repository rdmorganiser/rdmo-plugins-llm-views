from .utils import get_adapter


def render_tag(prompt, template, context):
    adapter = get_adapter()
    return adapter.on_render_tag(prompt, template, context)
