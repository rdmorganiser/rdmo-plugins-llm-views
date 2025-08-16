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

Add the following settings to your `config/settings/local.py` (and adjust them as required):

```python
INSTALLED_APPS = ['rdmo_llm_views', *INSTALLED_APPS]

LLM_TAGS_ADAPTER = 'rdmo_llm_views.adapter.langchain.LangChainAdapter'
LLM_TAGS_LANGCHAIN_SYSTEM_PROMPT = '''
You are a knowledgeable assistant specializing in writing data management plans (DMPs).

- Always produce output in Markdown format.
- Use headings, bullet points, where appropriate.
- Do not use tables.
- Do not use ```.
- Keep your response concise, not exceeding one page.
- Maintain a professional, clear, and concise writing style.
'''
LLM_TAGS_LANGCHAIN_USER_PROMPT = '''
Project data (JSON): {project}

Template: {template}

Prompt: {prompt}

Instructions:
- Fill the template with the project data.
- Take the prompt into account.
'''
LLM_TAGS_LANGCHAIN_LLM_SETTINGS = {
    "openai_api_key": OPENAI_API_KEY,
    "model": 'gpt-4o-mini'
}
```
