from django.conf import settings

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from rdmo.core.utils import markdown2html


class LangChainAdapter:

    def on_render(self, user_prompt):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("user", user_prompt)
            ]
        )

        chain = prompt | self.llm | self.parser

        result = chain.invoke({})

        return markdown2html(result)

    @property
    def llm(self):
        raise NotImplementedError

    @property
    def parser(self):
        return StrOutputParser()


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
