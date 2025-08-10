class BaseAdapter:
    def __init__(self, cl, settings):
        raise NotImplementedError

    def on_tag_render(self, prompt, template, project):
        raise NotImplementedError
