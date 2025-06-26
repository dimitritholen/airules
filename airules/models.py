"""Model registry for AI providers."""

from typing import Dict, List, Optional

MODELS = {
    "openai": [
        "gpt-4.1",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
    ],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "perplexity": [
        "sonar-pro",
    ],
}


def get_provider_for_model(model: str) -> Optional[str]:
    """Determine which provider a model belongs to."""
    for provider, models in MODELS.items():
        if model in models:
            return provider
    return None


def get_available_models(provider: Optional[str] = None) -> Dict[str, List[str]]:
    """Get available models, optionally filtered by provider."""
    if provider:
        return {provider: MODELS.get(provider, [])}
    return MODELS


def is_valid_model(model: str) -> bool:
    """Check if a model name is valid."""
    return get_provider_for_model(model) is not None


def format_models_list() -> str:
    """Format the models list for display."""
    lines = []
    for provider, models in MODELS.items():
        lines.append(f"\n[bold]{provider.upper()} Models:[/bold]")
        for model in models:
            lines.append(f"  • {model}")
    return "\n".join(lines)
