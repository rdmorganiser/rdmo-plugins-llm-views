from django import template
from django.template.loader import render_to_string
from django.utils.translation import get_language

from rdmo.core.utils import get_languages
from rdmo.views.templatetags.view_tags import get_set_value, get_set_values, get_value, get_values

from .nodes import LLMNode, RenderProjectExportNode

register = template.Library()


@register.tag('llm')
def llm(parser, token):
    return LLMNode.from_tag(parser, token, end_tag='endllm')


@register.simple_tag(takes_context=True)
def llm_reset(context):
    project = context.get('project')
    view = context.get('view')

    if project:
        project_id = project.id
        snapshot_id = project.snapshot['id'] if project.snapshot else None
        view_id = view['id']

        return render_to_string(
            'llm_views/tags/reset.html',
            {
                'project_id': project_id,
                'snapshot_id': snapshot_id,
                'view_id': view_id,
            },
        )
    else:
        return ''


@register.simple_tag()
def render_current_language():
    current_language = get_language()
    for lang_code, lang_string, _ in get_languages():
        if current_language == lang_code:
            return lang_string
    raise RuntimeError(f'Language "{current_language}" not found.')


@register.simple_tag(takes_context=True)
def render_project_export(context, project=None):
    return RenderProjectExportNode.from_simple_tag(project=project).render(context)


@register.tag('render_project_export_block')
def render_project_export_block(parser, token):
    return RenderProjectExportNode.from_tag(parser, token, end_tag='end_render_project_export_block')


@register.simple_tag(takes_context=True)
def format_value(context, attribute, set_prefix='', set_index=0, index=0, project=None):
    value = get_value(context, attribute, set_prefix=set_prefix, set_index=set_index, index=index, project=project)
    return format_string(value.get('value_and_unit', '')) if value else ''


@register.simple_tag(takes_context=True)
def format_value_list(context, attribute, set_prefix='', set_index=0, project=None):
    values = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return ', '.join(format_string(value.get('value_and_unit', '')) for value in values)


@register.simple_tag(takes_context=True)
def format_value_inline_list(context, attribute, set_prefix='', set_index=0, project=None):
    values = get_values(context, attribute, set_prefix=set_prefix, set_index=set_index, project=project)
    return ', '.join(format_string(value.get('value_and_unit', '')) for value in values)


@register.simple_tag(takes_context=True)
def format_set_value(context, set, attribute, set_prefix='', index=0, project=None):
    value = get_set_value(context, set, attribute, set_prefix=set_prefix, index=index, project=project)
    return format_string(value.get('value_and_unit', ''))


@register.simple_tag(takes_context=True)
def format_set_value_list(context, set, attribute, set_prefix='', project=None):
    values = get_set_values(context, set, attribute, set_prefix=set_prefix, project=project)
    return ', '.join(format_string(value.get('value_and_unit', '')) for value in values)


def format_string(string):
    return string.strip().replace('\n', ' ').replace('\t', ' ')
