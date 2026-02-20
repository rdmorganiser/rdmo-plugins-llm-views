from django.conf import settings

from rdmo.core.utils import markdown2html


class LangChainAdapter:

    def on_render(self, prompt, model):
        args = args = {
            **settings.LLM_VIEWS_LLM_ARGS,
            **({"model": model} if model is not None else {})
        }

        llm = self.get_llm(args)

        try:
            result = llm.invoke(prompt)
        except Exception as e:
            return str(e)

        return markdown2html(result.content)

    def get_llm(self, args):
        raise NotImplementedError


class OpenAILangChainAdapter(LangChainAdapter):

    def get_llm(self, args):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**args)


class OllamaLangChainAdapter(LangChainAdapter):

    def get_llm(self, args):
        from langchain_ollama import ChatOllama
        return ChatOllama(**args)
