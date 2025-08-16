from django.conf import settings

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from rdmo.core.utils import markdown2html

from . import BaseAdapter


class LangChainAdapter(BaseAdapter):
    def __init__(self):
        prompt = ChatPromptTemplate.from_messages(
            [("system", settings.LLM_TAGS_LANGCHAIN_SYSTEM_PROMPT), ("user", settings.LLM_TAGS_LANGCHAIN_USER_PROMPT)]
        )

        llm = ChatOpenAI(**settings.LLM_TAGS_LANGCHAIN_LLM_SETTINGS)

        parser = StrOutputParser()

        self.chain = prompt | llm | parser

    def on_tag_render(self, prompt, template, project):
        result = self.chain.invoke({"project": project, "template": template, "prompt": prompt})

        return markdown2html(result)
