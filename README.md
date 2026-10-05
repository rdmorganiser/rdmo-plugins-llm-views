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
pip install -e rdmo-plugins-llm-views[anthropic]  # alternatively
pip install -e rdmo-plugins-llm-views[mistralai]  # alternatively
pip install -e rdmo-plugins-llm-views[ollama]     # alternatively
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
    "model": 'meta-llama-3.1-8b-instruct'
}
```

For `anthropic` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.AnthropicLangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "api_key": ANTHROPIC_API_KEY,
    "model": 'claude-sonnet-4-6'
}
```

For `mistralai` use:

```python
LLM_VIEWS_ADAPTER = 'rdmo_llm_views.adapter.MistralAILangChainAdapter'
LLM_VIEWS_LLM_ARGS = {
    "api_key": MISTRALAI_API_KEY,
    "model": 'mistral-small-latest'
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
    'name': 'rdmo_llm_views',
    'workers': 4,
    'timeout': 300,
    'retry': 900,
    'compress': True,
    'save_limit': 0,
    'queue_limit': 1,
    'max_attempts': 1,
    'orm': 'default',
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

The django-q worker needs to be started in parallel to the usual `runserver` command:

```bash
python manage.py qcluster
```

### Production

Create a Systemd service file in `/etc/systemd/system/rdmo-qcluster.service`:

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
systemctl daemon-reload
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

The `{% render_current_language %}` can be used to access the current language (in RDMO) to use it in the instructions,
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

Adding `format="plain"` to the `llm` tag will skip the markdown conversion of the response and display the plain text. Using `format="pre"` will wrap the plain text in `<pre>` tags for debugging:

```django
{% llm format="pre" %}
...
{% endllm %}
```

### Example

Below, you find an example template for a `README` for a dataset.

```django
{% load view_tags %}
{% load llm_tags %}

<h1>Data Management Plan {% llm_reset %}</h1>

{% llm %}
You are a knowledgeable assistant specializing in writing data management plans (DMPs).

INSTRUCTIONS

Language & Style

* Produce all output in Markdown format.
* Translate the entire output to {% render_current_language %}.
* Use a professional, clear, and concise writing style.
* Use the past tense throughout.
* Paraphrase any "I"-formulations to refer to "the author(s)".
* Correct any typos found in the input.
* Provide full, syntactically correct sentences where running text is used.

Content Rules

* Fill the template only with context data from CONTEXT.
* If information is unavailable, insert `[bitte ergänzen]`.

Formatting Rules (strictly follow)

* Use h2 and h3 only where used in the template. Never use h1, h4, h5, or h6.
* Use `code` for all paths and file names.
* Format all dates in human-readable form.
* Always use (* + one space) for bullet lists.
* Always insert a blank line between a paragraph and a following bullet list.

CONTEXT

{% render_project_export %}

TEMPLATE

## 1. Data Summary

### Purpose of data collection

### Type and format of data

### Estimated volume

### Data origin

## 2. Standards and Metadata

### Metadata standards

### Documentation practices

### File naming and versioning conventions

## 3. Data Storage and Backup

### Active storage environment

### Backup strategy

### Security measures

## 4. Ethical, Legal, and Security Considerations

### Data sensitivity

### Informed consent and anonymization

### Compliance

## 5. Data Sharing and Access

### Sharing strategy

### Repositories

### Licensing

### Access control

## 6. Responsibilities and Resources

### Roles and responsibilities

### Expertise and training

### Budget

## 7. Data Preservation and Long-Term Archiving

### What will be preserved

### Duration

### Archiving solution

### Format sustainability

## 8. Quality Assurance

### Data quality checks

### Workflow transparency

### Change tracking

{% endllm %}
```
