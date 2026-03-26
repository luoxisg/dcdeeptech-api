"""
Provider router: maps a ModelProvider enum value to the correct adapter instance.
Add new adapters here as providers are onboarded.
"""
from app.adapters.base import BaseAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.adapters.vllm_adapter import VLLMAdapter
from app.models.model_catalog import ModelProvider

# Singleton adapter instances (stateless, safe to reuse across requests)
_adapters: dict[ModelProvider, BaseAdapter] = {
    ModelProvider.openrouter: OpenRouterAdapter(),
    ModelProvider.vllm: VLLMAdapter(),
}


def get_adapter(provider: ModelProvider) -> BaseAdapter:
    """
    Return the adapter for the given provider.
    Raises NotImplementedError for unrecognised providers.
    """
    adapter = _adapters.get(provider)
    if adapter is None:
        raise NotImplementedError(f"No adapter registered for provider: {provider}")
    return adapter
