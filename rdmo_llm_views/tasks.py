from .utils import get_adapter


def render_template(**kwargs):
    return get_adapter().on_render_template(**kwargs)


def render_prompt(**kwargs):
    return get_adapter().on_render_prompt(**kwargs)
