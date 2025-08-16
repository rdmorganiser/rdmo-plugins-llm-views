from django.conf import settings

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rdmo.core.utils import markdown2html

from . import BaseAdapter


class LangChainAdapter(BaseAdapter):
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", settings.LLM_VIEWS_SYSTEM_PROMPT),
                ("user", settings.LLM_VIEWS_USER_PROMPT)
            ]
        )

        self.parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.parser

    def on_tag_render(self, prompt, template, project):
        result = self.chain.invoke({
            "project": project,
            "template": template,
            "prompt": prompt
        })

        return markdown2html(result)

    @property
    def llm(self):
        raise NotImplementedError


class OpenAILangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**settings.LLM_VIEWS_LLM_ARGS)


class OllamaLangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**settings.LLM_VIEWS_LLM_ARGS)
