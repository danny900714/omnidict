import inspect
from pathlib import Path
from typing import Any

import yaml
from pytest import Config, StashKey

from omnidict.provider import Provider, _providers

# Stash keys
specs_key = StashKey[dict[str, dict[str, Any]]]()
providers_key = StashKey[dict[str, type[Provider]]]()


def pytest_configure(config: Config):
    # Store all provider test specs into stash
    specs = dict[str, dict[str, Any]]()
    for spec_path in Path(__file__).parent.glob("*/spec.yaml"):
        provider_id = spec_path.parent.name
        with open(spec_path) as f:
            specs[provider_id] = yaml.safe_load(f)
    config.stash[specs_key] = specs

    # Store all provider classes into stash
    providers = dict[str, type[Provider]]()
    for _, klass in inspect.getmembers(_providers, inspect.isclass):
        if issubclass(klass, Provider):
            providers[klass.id()] = klass
    config.stash[providers_key] = providers
