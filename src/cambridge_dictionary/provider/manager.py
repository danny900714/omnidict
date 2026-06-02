import inspect
from typing import Optional

from . import _providers
from .common import Provider


class ProviderManager:
    def __init__(self, config: dict):
        self._providers: dict[str, Provider] = {}

        self._provider_classes: dict[str, tuple[str, type[Provider]]] = {}
        for (_, klass) in inspect.getmembers(_providers, inspect.isclass):
            provider_id = klass.id()
            provider_name = klass.name()
            self._provider_classes[provider_id] = (provider_name, klass)

        self._providers_config: Optional[dict] = None
        if "providers" in config:
            self._providers_config = config

    def get_provider(self, provider_id: str) -> Provider | None:
        if provider_id not in self._providers:
            if provider_id in self._provider_classes:
                klass = self._provider_classes[provider_id][1]
                self._providers[provider_id] = self._instantiate_provider(klass)

        return self._providers.get(provider_id)

    def _instantiate_provider(self, klass: type[Provider]) -> Provider:
        provider = klass()
        if self._providers_config is not None and klass.id() in self._providers_config:
            provider.config = self._providers_config[klass.id()]

        return provider
