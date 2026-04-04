import json
import logging

from django.conf import settings

from langchain_core.messages import message_to_dict

from rdmo.core.utils import markdown2html

logger = logging.getLogger(__name__)
logger_usage = logging.getLogger('rdmo_llm_views.usage')


class LangChainAdapter:
    def on_render(self, prompt, model):
        args = {**settings.LLM_VIEWS_LLM_ARGS, **({'model': model} if model is not None else {})}

        logger.debug('model="%s" prompt="%s"', args.get('model'), prompt)

        llm = self.get_llm(args)

        try:
            result = llm.invoke(prompt)

            result_dict = message_to_dict(result)
            logger.debug('result = %s', json.dumps(result_dict, indent=2))

            usage_metadata = result_dict.get('data', {}).get('usage_metadata', {})
            logger_usage.info(json.dumps({'model': args.get('model'), **usage_metadata}))

        except Exception as e:
            logger.exception(e)
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
