import os
import json
import logging
from typing import Type, TypeVar
from pydantic import BaseModel
from litellm import completion
from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self):
        if settings.api_key:
            if settings.llm_provider.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = settings.api_key
            elif settings.llm_provider.lower() == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = settings.api_key
            elif settings.llm_provider.lower() == "gemini":
                os.environ["GEMINI_API_KEY"] = settings.api_key
            
        # Optional: default mapping or explicit model string
        if "/" not in settings.llm_model and settings.llm_provider:
            self.model = f"{settings.llm_provider}/{settings.llm_model}"
        else:
            self.model = settings.llm_model

    def generate_text(self, prompt: str) -> str:
        """Basic text generation."""
        try:
            logger.debug(f"Generating text using {self.model}")
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=settings.timeout
            )
            return str(response.choices[0].message.content)
        except Exception as e:
            error_str = str(e)
            if settings.api_key and settings.api_key in error_str:
                error_str = error_str.replace(settings.api_key, "***REDACTED***")
            logger.error(f"Error in LLM generation: {error_str}")
            raise RuntimeError(error_str) from None

    def generate_structured_output(self, prompt: str, schema: Type[T]) -> T:
        """Generate structured output validating against a Pydantic schema."""
        try:
            logger.debug(f"Generating structured output for {schema.__name__} using {self.model}")
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=schema,
                timeout=settings.timeout
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty content")
                
            # If the provider natively supports structured output, LiteLLM handles it and returns a JSON string
            data = json.loads(content)
            return schema(**data)
        except Exception as e:
            error_str = str(e)
            if settings.api_key and settings.api_key in error_str:
                error_str = error_str.replace(settings.api_key, "***REDACTED***")
            logger.error(f"Error in structured LLM generation: {error_str}")
            raise RuntimeError(error_str) from None
