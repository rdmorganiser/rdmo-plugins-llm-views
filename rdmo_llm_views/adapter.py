import json
import logging
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from langchain_core.messages import message_to_dict
from markdown import markdown

logger = logging.getLogger(__name__)
logger_usage = logging.getLogger('rdmo_llm_views.usage')


class LangChainAdapter:
    def invoke(self, prompt, model=None):
        args = {**settings.LLM_VIEWS_LLM_ARGS, **({'model': model} if model is not None else {})}

        logger.debug('prompt="%s"', prompt)

        llm = self.get_llm(args)

        try:
            start_time = timezone.now()
            start_perf = time.perf_counter()

            result = llm.invoke(prompt)

            end_time = timezone.now()
            end_perf = time.perf_counter()

            result_dict = message_to_dict(result)
            result_dict['data']['time'] = {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'elapsed_time': round(end_perf - start_perf, 1),
            }

            logger.debug('result = %s', json.dumps(result_dict, indent=2))
            logger_usage.info(
                json.dumps(
                    {
                        'model': result_dict['data']['response_metadata']['model_name'],
                        'elapsed_time': result_dict['data']['time']['elapsed_time'],
                        **{
                            key: result_dict['data']['usage_metadata'][key]
                            for key in ('input_tokens', 'output_tokens', 'total_tokens')
                        },
                    }
                )
            )

            return result_dict

        except Exception as e:
            logger.exception(e)
            return str(e)

    def get_llm(self, args):
        raise NotImplementedError

    def render_metadata(self, result_dict):
        if isinstance(result_dict, dict):
            return render_to_string('llm_views/tags/metadata.html', {'result': result_dict})
        else:
            return ''

    def render_content(self, result_dict, result_format):
        if isinstance(result_dict, dict):
            if result_format == 'markdown':
                return markdown(result_dict['data']['content'])
            elif result_format == 'pre':
                return f'<pre>{result_dict["data"]["content"]}</pre>'
            else:
                return result_dict['data']['content']
        else:
            return render_to_string('llm_views/tags/error.html', {'result': result_dict})


class OpenAILangChainAdapter(LangChainAdapter):
    def get_llm(self, args):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**args)


class OllamaLangChainAdapter(LangChainAdapter):
    def get_llm(self, args):
        from langchain_ollama import ChatOllama

        return ChatOllama(**args)


class AnthropicLangChainAdapter(LangChainAdapter):
    def get_llm(self, args):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(**args)


class MistralAILangChainAdapter(LangChainAdapter):
    def get_llm(self, args):
        from langchain_mistralai import ChatMistralAI

        print(args)
        return ChatMistralAI(**args)
