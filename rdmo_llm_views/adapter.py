from django.conf import settings

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from rdmo.core.utils import markdown2html


class BaseAdapter:

    def __init__(self, cl, settings):
        raise NotImplementedError

    def on_tag_render(self, prompt, template, context):
        raise NotImplementedError


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

    def on_tag_render(self, prompt, template, context):
        result = self.chain.invoke({
            "context": context,
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
