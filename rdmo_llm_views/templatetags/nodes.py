from urllib.parse import urlparse

from django.conf import settings
from django.template import Node as BaseNode
from django.template.loader import render_to_string

from django_q.models import OrmQ, Task
from django_q.tasks import async_task

from ..utils import get_adapter, get_group, get_hash, get_project_export

adapter = get_adapter()


class Node(BaseNode):
    def __init__(self, nodelist=None, kwargs=None, unresolved_kwargs=None):
        self.nodelist = nodelist
        self.kwargs = kwargs or {}
        self.unresolved_kwargs = unresolved_kwargs or {}

    def render_content(self, context):
        return self.nodelist.render(context) if self.nodelist is not None else None

    def resolve_kwargs(self, context):
        if self.kwargs:
            return self.kwargs
        else:
            return {k: v.resolve(context) for k, v in self.unresolved_kwargs.items()}

    @classmethod
    def from_tag(cls, parser, token, end_tag):
        _, *tag_args = token.split_contents()

        unresolved_kwargs = {}
        for tag_arg in tag_args:
            if '=' in tag_arg:
                key, value = tag_arg.split('=', 1)
                unresolved_kwargs[key] = parser.compile_filter(value)

        nodelist = parser.parse((end_tag,))
        parser.delete_first_token()
        return cls(nodelist=nodelist, unresolved_kwargs=unresolved_kwargs)

    @classmethod
    def from_simple_tag(cls, **kwargs):
        return cls(kwargs=kwargs)


class LLMNode(Node):
    def render(self, context):
        kwargs = self.resolve_kwargs(context)
        prompt = self.render_content(context)

        project = kwargs.get('project') or context.get('project')
        view = context.get('view')
        model = kwargs.get('model') if getattr(settings, 'LLM_VIEWS_SELECT_MODEL', False) else None
        system_prompt = context.get('system_prompt', '')

        if not project or kwargs.get('verbatim') == 'true':
            return f'<pre>{prompt}</pre>'

        project_id = project.id
        snapshot_id = project.snapshot['id'] if project.snapshot else None
        view_id = view['id']

        if kwargs.get('type') == 'system':
            context['system_prompt'] = system_prompt + prompt
            return ''

        task_func = 'rdmo_llm_views.tasks.invoke'
        task_kwargs = {
            'prompt': system_prompt + prompt,
            'model': model,
        }

        task_name = get_hash(project_id, snapshot_id, view_id, **task_kwargs)
        task_group = get_group(project_id, snapshot_id, view_id)

        # check if a task with this name has already be computed
        task = Task.objects.filter(name=task_name).first()

        if task:
            result_format = kwargs.get('format', 'markdown')

            if kwargs.get('metadata') == 'true':
                return adapter.render_metadata(task.result) + adapter.render_content(task.result, result_format)
            else:
                return adapter.render_content(task.result, result_format)

        else:
            # check if there is a queued task with that name
            if task_name not in [queued_task.name() for queued_task in OrmQ.objects.all()]:
                async_task(task_func, task_name=task_name, group=task_group, **task_kwargs)

            return render_to_string(
                'llm_views/tags/loading.html',
                {
                    'project_id': project_id,
                    'snapshot_id': snapshot_id,
                    'view_id': view_id,
                    'timeout': settings.LLM_VIEWS_TIMEOUT,
                },
            )


class RenderProjectExportNode(Node):
    def render(self, context):
        kwargs = self.resolve_kwargs(context)
        content = self.render_content(context)

        project = kwargs.get('project') or context.get('project')

        uris = set() if content is None else {string for string in content.split() if self.is_uri(string)}

        return get_project_export(project, uris=uris)

    def is_uri(self, string):
        try:
            result = urlparse(string)
        except (ValueError, AttributeError):
            return False

        return result.scheme in ('http', 'https') and bool(result.netloc)
