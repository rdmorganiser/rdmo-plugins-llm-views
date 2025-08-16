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
pip install -e rdmo-plugins-llm-views
```

Add the following settings to your `config/settings/local.py`:

```python
INSTALLED_APPS = ['rdmo_llm_views', *INSTALLED_APPS]

LLM_TAGS_ADAPTER = 'rdmo_llm_views.adapter.langchain.LangChainAdapter'
LLM_TAGS_LANGCHAIN_SYSTEM_PROMPT = '''
    You are a helpful assistant that writes data management plans.
    You will always produce markdown output.
'''
LLM_TAGS_LANGCHAIN_USER_PROMPT = '''
    Project data:
    ```json
    {project}
    ```

    Template: {template}

    Prompt: {prompt}

    Please produce the requested output.
'''
LLM_TAGS_LANGCHAIN_LLM_SETTINGS = {
    "openai_api_key": OPENAI_API_KEY,
    "model": 'gpt-3.5-turbo'
}
```
