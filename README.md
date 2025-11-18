rdmo-plugins-llm-views
======================

Setup
-----

The setup assumes that `rdmo-app` is already configured. First, install the plugin

```bash
# directly from github
pip install git+https://github.com/rdmorganiser/rdmo-plugins-llm-views

# alternatively, from a local copy
git clone git@github.com:rdmorganiser/rdmo-plugins-llm-views
pip install -e rdmo-plugins-llm-views[openai]
pip install -e rdmo-plugins-llm-views[ollama]  # alternatively
```

Add the following settings to your `config/settings/local.py` (and adjust them as required):

```python
INSTALLED_APPS = ['rdmo_llm_views', *INSTALLED_APPS]

LLM_VIEWS_LANGCHAIN_SYSTEM_PROMPT = '''
You are a knowledgeable assistant specializing in writing data management plans (DMPs).

- Always produce output in Markdown format.
- Use headings, bullet points, where appropriate.
- Do not use tables.
- Do not use ```.
- Keep your response concise, not exceeding one page.
- Maintain a professional, clear, and concise writing style.
'''
LLM_VIEWS_LANGCHAIN_USER_PROMPT = '''
Project data (JSON): {project}

Template: {template}

Prompt: {prompt}

Instructions:
- Fill the template with the project data.
- Take the prompt into account.
'''
```

For `openai` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.OpenAILangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "openai_api_key": OPENAI_API_KEY,
    "model": 'gpt-4o-mini'
}
```

For `ollama` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.OllamaLangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "model": "gemma3:1b"
}
```

Usage
-----

The `{% llm %}` tag can be used in two ways.

```django
{% load view_tags %}
{% load llm_tags %}

{% llm %}
## 1. Data Summary

### Purpose of data collection

...

{% endllm %}
```

An additional prompt can be provided, e.g.:

```django
{% load view_tags %}
{% load llm_tags %}

{% llm prompt="Write in the style the lord of the rings. Use only h2 and h3." %}
## 1. Data Summary

### Purpose of data collection

...

{% endllm %}
```

For a more fine grained control, the attributes can be selected. The model is then provided only with the questions and
answers for this attribute.

```django
{% load view_tags %}
{% load llm_tags %}

{% llm attributes='project/research_question/title,project/research_question/keywords'  %}
The title of the project is ... Keywords are ...
{% endllm %}

...
```
