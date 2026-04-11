from .utils import get_adapter


def invoke(**kwargs):
    return get_adapter().invoke(**kwargs)
