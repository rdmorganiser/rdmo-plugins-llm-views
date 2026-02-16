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

LLM_VIEWS_TIMEOUT = 4000
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
