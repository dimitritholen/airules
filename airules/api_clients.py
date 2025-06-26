"""API clients for different AI providers."""

import os
from abc import ABC, abstractmethod
from typing import Dict, Protocol

import anthropic
import openai

from .exceptions import APIError
from .models import get_provider_for_model


class AIClientProtocol(Protocol):
    """Protocol for AI client implementations."""

    def generate_completion(self, prompt: str, model: str) -> str:
        """Generate completion using the AI model."""
        ...


class BaseAIClient(ABC):
    """Base class for AI clients."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def generate_completion(self, prompt: str, model: str) -> str:
        """Generate completion using the AI model."""
        pass

    def _validate_api_key(self) -> None:
        """Validate that API key is present."""
        if not self.api_key:
            raise APIError(f"API key not provided for {self.__class__.__name__}")


class OpenAIClient(BaseAIClient):
    """OpenAI API client."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._validate_api_key()
        self.client = openai.OpenAI(api_key=api_key)

    def generate_completion(self, prompt: str, model: str) -> str:
        """Generate completion using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in generating rules for AI coding assistants. Your output must be only the raw markdown content for the rules file.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise APIError(f"OpenAI API error: {e}")


class AnthropicClient(BaseAIClient):
    """Anthropic API client."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._validate_api_key()
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_completion(self, prompt: str, model: str) -> str:
        """Generate completion using Anthropic API."""
        try:
            system_prompt = "You are an expert in generating rules for AI coding assistants. Your output must be only the raw markdown content for the rules file."

            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": f"{system_prompt}\n\n{prompt}",
                    }
                ],
            )
            return response.content[0].text  # type: ignore
        except Exception as e:
            raise APIError(f"Anthropic API error: {e}")


class PerplexityClient(BaseAIClient):
    """Perplexity API client for research."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._validate_api_key()
        self.client = openai.OpenAI(
            api_key=api_key, base_url="https://api.perplexity.ai"
        )

    def generate_completion(self, prompt: str, model: str = "sonar-pro") -> str:
        """Generate completion using Perplexity API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that provides concise, expert-level summaries for software development best practices.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise APIError(f"Perplexity API error: {e}")


class AIClientFactory:
    """Factory for creating AI clients."""

    _client_cache: Dict[str, BaseAIClient] = {}

    @classmethod
    def get_client(cls, model: str) -> BaseAIClient:
        """Get the appropriate client for a model."""
        provider = get_provider_for_model(model)

        if not provider:
            raise APIError(f"Unknown model: {model}")

        # Check cache first
        if provider in cls._client_cache:
            return cls._client_cache[provider]

        # Create new client
        client = cls._create_client(provider)
        cls._client_cache[provider] = client
        return client

    @classmethod
    def _create_client(cls, provider: str) -> BaseAIClient:
        """Create a client for the specified provider."""
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise APIError(
                    "Missing OpenAI API Key. Set OPENAI_API_KEY environment variable."
                )
            return OpenAIClient(api_key)

        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise APIError(
                    "Missing Anthropic API Key. Set ANTHROPIC_API_KEY environment variable."
                )
            return AnthropicClient(api_key)

        elif provider == "perplexity":
            api_key = os.environ.get("PERPLEXITY_API_KEY")
            if not api_key:
                raise APIError(
                    "Missing Perplexity API Key. Set PERPLEXITY_API_KEY environment variable."
                )
            return PerplexityClient(api_key)

        else:
            raise APIError(f"Unsupported provider: {provider}")

    @classmethod
    def get_research_client(cls) -> PerplexityClient:
        """Get Perplexity client for research."""
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise APIError(
                "Missing Perplexity API Key. Set PERPLEXITY_API_KEY environment variable."
            )
        return PerplexityClient(api_key)
