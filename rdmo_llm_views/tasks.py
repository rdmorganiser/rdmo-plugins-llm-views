from .utils import get_adapter


def render(**kwargs):
    return get_adapter().on_render(**kwargs)
