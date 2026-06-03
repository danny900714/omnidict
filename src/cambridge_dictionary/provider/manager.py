import inspect
from dataclasses import dataclass

from . import _providers
from .common import Provider, DictionaryInfo


@dataclass
class _ProviderInfo:
    klass: type[Provider]
    name: str
    dictionaries: dict[str, DictionaryInfo]
    icon: str | None = None


class ProviderManager:
    def __init__(self):
        self._providers: dict[str, Provider] = {}

        self._provider_catalog: dict[str, _ProviderInfo] = {}
        for (_, klass) in inspect.getmembers(_providers, inspect.isclass):
            if issubclass(klass, Provider):
                provider_id = klass.id()
                provider_name = klass.name()
                provider_dictionaries = klass.supported_dictionaries()
                provider_icon = klass.icon()
                self._provider_catalog[provider_id] = _ProviderInfo(klass, provider_name, provider_dictionaries,
                                                                    provider_icon)

    def get_provider(self, provider_id: str) -> Provider | None:
        if provider_id not in self._providers:
            if provider_id in self._provider_catalog:
                self._providers[provider_id] = self._instantiate_provider(self._provider_catalog[provider_id].klass)

        return self._providers.get(provider_id)

    def clear_providers(self):
        self._providers.clear()

    @staticmethod
    def _instantiate_provider(klass: type[Provider]) -> Provider:
        from ..globals import config

        provider = klass()
        if config is not None:
            provider_config = config.get("providers", {}).get(klass.id())
            provider.config = provider_config

        return provider
