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
pip install -e rdmo-plugins-llm-views[anthopic]
pip install -e rdmo-plugins-llm-views[ollama]  # alternatively
```

Add the following settings to your `config/settings/local.py` (and adjust them as required):

```python
INSTALLED_APPS = ['rdmo_llm_views', *INSTALLED_APPS]
```

In addition, the llm views endpoints needs to be added to the `config/urls.py`

```python
urlpatterns += [path('api/v1/', include('rdmo_llm_views.urls'))]
```

For `openai` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.OpenAILangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "openai_api_key": OPENAI_API_KEY,
    "model": 'gpt-5.4-mini'
}
```

or, for the [ChatAI](https://academiccloud.de/de/services/chatai/) service of the
[Academic Cloud](https://academiccloud.de), use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.OpenAILangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    'api_key': CHATAI_API_KEY,
    'base_url': 'https://chat-ai.academiccloud.de/v1',
    "model": 'meta-llama-31-8b-instruct'
}
```

For `anthopic` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.AnthropicLangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "api_key": ANTHROPIC_API_KEY,
    "model": 'claude-sonnet-4-6'
}
```

For `ollama` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.OllamaLangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "model": "qwen3.5:4b"
}
```

In order to use [django-q](https://django-q.readthedocs.io) to perform the call to the LLM asynchronous, the following
settings need to be added:

```python
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}
```

Additionally the following settings can be used:

```python
LLM_VIEWS_SELECT_MODEL = True  # enable model selection in the view
LLM_VIEWS_TIMEOUT = 4000       # timeout for polling
```

Usage
-----

### Development

The djqngo-q worker needs to be started in parallel to the usual `runserver` command:

```bash
python manage.py qcluster
```

### Production

Create a Systed service file in `/etc/systemd/system/rdmo-qcluster.service`:

```
[Unit]
Description=RDMO qcluster runner
After=network.target

[Service]
User=rdmo
Group=rdmo

LogsDirectory=django-q

WorkingDirectory=/srv/rdmo/rdmo-app/

ExecStart=/srv/rdmo/rdmo-app/env/bin/python manage.py qcluster

StandardOutput=append:/var/log/django-q/stdout.log
StandardError=append:/var/log/django-q/stderr.log

[Install]
WantedBy=multi-user.target
```

Reload and enable the service:

```bash
sys0temctl daemon-reload
systemctl enable --now rdmo-qcluster
```

### Views

The `{% llm %}` tag is used in the following way:

```django
{% load view_tags %}
{% load llm_tags %}

{% llm %}
You are a knowledgeable assistant specializing in ...

Instructions:
- Follow only the instructions from this prompt.
...

Context data (JSON):

{% render_project_export %}

Template:

## 1. Data Summary

### Purpose of data collection

...

{% endllm %}
```

The `{% render_project_export %}` tag is replaced with a serialization of the whole project. Alternatively, the following
format tags can be used to render specific values into the prompt (similar to the
[render functions](https://rdmo.readthedocs.io/en/latest/management/views.html#render-values) of regular RDMO views.

* `format_value`
* `format_value_list`
* `format_value_inline_list`
* `format_set_value`
* `format_set_value_list`

The `{% format_current_language %}` can be used to access the current language (in RDMO) to use it in the instructions,
e.g.:

```django
Instructions:
...
- Translate the whole output to {% render_current_language %}.
```

The current date can be accessed using the regular Django
[now](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#now) tag, e.g.:

```django
This document was created on {% now "Y-m-d" %}.
```

If `LLM_VIEWS_SELECT_MODEL = True` is set in the RDMO settings, the model can be selected in the `llm` tag:

```django
{% llm model="openai-gpt-oss-120b" %}
...
{% endllm %}
```

Each `llm` tag is send to the LLM separately. Tags with `type="system"` are not send to the LLM but prepended to all
**other** LLM calls:

```django
{% llm type="system" %}
You are a knowledgeable assistant specializing in ...

Instructions:
- Follow only the instructions from this prompt.
...
{% endllm %}

{% llm %}
Template:
...
{% endllm %}

{% llm %}
Template:
...
{% endllm %}
```

If you add `verbatim="true"` to the `llm` tag, the prompt will not be send to the llm, but just printed in verbatim:

```django
{% llm verbatim="true" %}
...
{% endllm %}
```

If you add `metadata="true"` to the `llm` tag, additional metadata information will be rendered on top of the view:

```django
{% llm metadata="true" %}
...
{% endllm %}
```
