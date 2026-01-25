import sys
import json
import openai
import logging
import traceback
import time

from src.utils import convert_tools_alphachat

logger = logging.getLogger(__name__)

class AbstractModelAPIExecutor:
    """
    A base class for model API executors that defines a common interface for making predictions.
    This class should be inherited by specific API executor implementations.

    Attributes:
        model (str): The model identifier.
        api_key (str): The API key for accessing the model.
    """
    def __init__(self, model, api_key):
        logger.info(f"model: {model}")
        logger.info(f"api_key: {api_key}")
        self.model = model
        self.api_key = api_key

    def predict(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def _sanitize_messages(self, messages, for_mistral=False):
        """
        Sanitizes messages by replacing invalid tool call IDs (like 'random_id')
        with valid alphanumeric IDs to satisfy API requirements.
        
        Args:
            messages: List of message dictionaries
            for_mistral: If True, generates Mistral-compatible 9-char alphanumeric IDs
        """
        if not messages:
            return messages
            
        sanitized = []
        
        # Mistral은 정확히 9자리 영숫자 ID 필요 (a-z, A-Z, 0-9)
        if for_mistral:
            import random
            import string
            valid_id = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        else:
            # 일반적인 경우 (call_ prefix 포함 가능)
            valid_id = "call_abc123"
        
        for msg in messages:
            new_msg = msg.copy()
            if 'tool_calls' in new_msg and new_msg['tool_calls']:
                new_tool_calls = []
                for tc in new_msg['tool_calls']:
                    new_tc = tc.copy()
                    if new_tc.get('id') == 'random_id':
                        new_tc['id'] = valid_id
                    new_tool_calls.append(new_tc)
                new_msg['tool_calls'] = new_tool_calls
            
            if new_msg.get('role') == 'tool' and new_msg.get('tool_call_id') == 'random_id':
                new_msg['tool_call_id'] = valid_id
                
            sanitized.append(new_msg)
        return sanitized

    def _call_with_retry(self, func, *args, **kwargs):
        # 기본 재시도 횟수를 늘려 429(분당 제한 등)에 더 강인하게 대응
        max_retries = kwargs.pop('max_retries', 8)
        for attempt in range(max_retries):
            try:
                response = func(*args, **kwargs)
                response = response.model_dump()
                return response
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                # 크레딧 부족(402) / 인증(401) 등은 재시도해도 해결 안 됨 → 즉시 실패
                status_code = getattr(e, "status_code", None)
                if status_code in (401, 402, 403):
                    logger.error(f"API call failed (non-retriable {status_code}) ({error_type}): {error_msg[:300]}")
                    raise e
                if attempt < max_retries - 1:
                    # 429 등 일시적 제한에 대비: 4s/8s/16s... 지수 백오프
                    base_delay = 4
                    wait_time = base_delay * (2 ** attempt)
                    # 과도한 대기 방지 (상한 60초)
                    wait_time = min(wait_time, 60)
                    logger.warning(f"API call failed ({error_type}): {error_msg[:200]}")
                    logger.warning(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {max_retries} attempts: {error_type}: {error_msg}")
                    raise e

    def _parse_response(self, response):
        """
        Parses the API response and extracts relevant information.
        Returns a dictionary that includes both simplified fields and 
        the original OpenAI-style structure for compatibility.
        """
        if not response or not response.get('choices'):
            return {"content": None, "role": "assistant", "tool_calls": None, "choices": []}

        choice = response['choices'][0]
        message = choice['message']
        
        # 원본 구조 유지 (formatter.py 등에서 사용)
        parsed = response.copy()
        
        # 편리한 접근을 위한 필드 추가
        parsed.update({
            "content": message.get("content"),
            "role": message.get("role", "assistant"),
            "tool_calls": message.get("tool_calls"),
            "function_call": message.get("function_call"),
            "tool_call_id": None,
            "name": None
        })
        return parsed

    def models(self):
        """모델 리스트 조회 (기본 구현)"""
        return []


class OpenaiModelAzureAPI(AbstractModelAPIExecutor):
    def __init__(self, model, api_key, api_version, api_base):
        super().__init__(model, api_key)
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=api_base
        )
        self.openai_chat_completion = self.client.chat.completions.create

    def models(self):
        return self.client.models.list()

    def predict(self, api_request):
        kwargs = {
            "model": self.model,
            "temperature": api_request["temperature"],
            "messages": api_request["messages"],
            "tools": api_request.get("tools"),
            "n": int(api_request.get("n", 1) or 1),
        }
        if api_request.get("max_tokens") is not None:
            kwargs["max_tokens"] = int(api_request["max_tokens"])
        response = self._call_with_retry(self.openai_chat_completion, **kwargs)
        response_output = self._parse_response(response)
        return response_output


class OpenaiModelAPI(AbstractModelAPIExecutor):
    def __init__(self, model, api_key, base_url=None):
        """
        Initialize the OpenaiModelAPI class.

        Parameters:
        model (str): The name of the model to use.
        api_key (str): The API key for authenticating with OpenAI API.
        base_url (str, optional): The base URL for the API endpoint (for custom endpoints).
        """
        super().__init__(model, api_key)
        if base_url:
            self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        else:
            self.client = openai.OpenAI(api_key=api_key)
        self.openai_chat_completion = self.client.chat.completions.create

    def models(self):
        """OpenAI 모델 리스트 조회"""
        try:
            return self.client.models.list()
        except Exception:
            return []

    def predict(self, api_request):
        messages = self._sanitize_messages(api_request['messages'])
        kwargs = {
            "model": self.model,
            "temperature": api_request["temperature"],
            "messages": messages,
            "tools": api_request.get("tools"),
            "n": int(api_request.get("n", 1) or 1),
        }
        if api_request.get("max_tokens") is not None:
            kwargs["max_tokens"] = int(api_request["max_tokens"])
        response = self._call_with_retry(self.openai_chat_completion, **kwargs)
        response_output = self._parse_response(response)
        return response_output


class OpenRouterModelAPI(AbstractModelAPIExecutor):
    def __init__(self, model, api_key, base_url):
        """
        Initialize the OpenRouterModelAPI class.

        Parameters:
        model (str): The name of the model to use (e.g., meta-llama/llama-3.3-70b-instruct).
        api_key (str): The API key for authenticating with OpenRouter.
        base_url (str): The base URL for the OpenRouter API endpoint.
        """
        super().__init__(model, api_key)
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/mink555/mcp-llm-bm-v1",
                "X-Title": "FunctionChat-Bench Evaluation"
            }
        )
        self.openai_chat_completion = self.client.chat.completions.create

    def models(self):
        """OpenRouter 모델 리스트 조회"""
        try:
            return self.client.models.list()
        except Exception:
            # 모델 리스트 조회 실패 시 빈 리스트 반환
            return []

    def predict_tool(self, api_request):
        # OpenRouter API 호출 전 1초 딜레이
        time.sleep(1.0)
        
        tools = api_request.get('tools')
        
        # Mistral 모델인 경우 9자리 영숫자 ID로 normalize
        is_mistral = 'mistral' in self.model.lower()
        messages = self._sanitize_messages(api_request['messages'], for_mistral=is_mistral)
        
        response = self._call_with_retry(
            self.openai_chat_completion,
            model=self.model,
            temperature=api_request['temperature'],
            messages=messages,
            tools=tools
        )
        response_output = self._parse_response(response)
        return response_output

    def predict(self, api_request):
        """OpenRouter API를 통한 예측"""
        return self.predict_tool(api_request)


class APIExecutorFactory:
    """
    A factory class to create model API executor instances based on the model name.
    """

    @staticmethod
    def get_model_api(model_name, api_key=None, served_model_name=None, base_url=None, gcloud_project_id=None, gcloud_location=None):
        """
        Creates and returns an API executor for a given model.

        Parameters:
            model_name (str): The name of the model to be used.
            api_key (str, optional): The API key required for authentication.
            served_model_name (str, optional): served model name (not used for OpenRouter).
            base_url (str, optional): The base URL of the API service.
            gcloud_project_id (str, optional): Not used (kept for compatibility).
            gcloud_location (str, optional): Not used (kept for compatibility).

        Returns:
            An instance of an API executor for the specified model.

        Raises:
            ValueError: If the model name is not supported.
        """
        # OpenRouter API를 우선 확인 (base_url에 openrouter.ai가 포함된 경우)
        if base_url and 'openrouter.ai' in base_url:
            return OpenRouterModelAPI(model_name, api_key, base_url)
        
        # OpenAI 모델 (평가용 LLM-as-Judge)
        if model_name.lower().startswith('gpt'):
            return OpenaiModelAPI(model_name, api_key, base_url)
        
        # 기본적으로 OpenRouter 사용 (base_url이 제공된 경우)
        if base_url:
            return OpenRouterModelAPI(model_name, api_key, base_url)
        
        # 그 외의 경우 OpenAI로 시도 (평가용)
        return OpenaiModelAPI(model_name, api_key)
