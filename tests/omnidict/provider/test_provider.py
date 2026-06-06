import base64
import time
from pydoc import locate
from typing import Any, cast

import orjson
import pytest
import requests.sessions
from pytest import Metafunc, Config, FixtureRequest, MonkeyPatch

from omnidict.provider import Provider
from omnidict.provider.common import DictionaryInfo, Definition
from .conftest import providers_key, specs_key


def _build_dictionary_specs(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dictionaries = spec.get("dictionaries", {})
    for _, dictionary_spec in dictionaries.items():
        # Set mode and interval of dictionary scope to global settings
        dictionary_spec.setdefault("config", spec.get("config"))
        dictionary_spec.setdefault("mode", spec.get("mode", "online"))
        dictionary_spec.setdefault("interval", spec.get("interval", 0))
    return dictionaries


def _build_test_cases(provider_id: str, config: Config) -> list[tuple[Provider, str, dict[str, Any]]]:
    specs = config.stash[specs_key]
    providers = config.stash[providers_key]

    spec = specs[provider_id]
    provider = providers[provider_id]()

    test_cases = []
    for dictionary_id, dictionary_spec in _build_dictionary_specs(spec).items():
        provider.config = dictionary_spec.get("config")
        test_cases.append((provider, dictionary_id, dictionary_spec))
    return test_cases


def _bytes_encode(obj: Any) -> Any:
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Cannot serialize object of {type(obj)}")


def pytest_generate_tests(metafunc: Metafunc):
    if metafunc.cls and issubclass(metafunc.cls, TestProvider):
        if metafunc.fixturenames == ["klass"]:
            metafunc.parametrize("klass", metafunc.config.stash[providers_key].values())
        elif metafunc.fixturenames == ["provider", "dictionary_id", "spec"]:
            specs = metafunc.config.stash[specs_key]

            params = []
            ids = []
            for provider_id, spec in specs.items():
                for (provider, dictionary_id, dictionary_spec) in _build_test_cases(provider_id, metafunc.config):
                    params.append((provider, dictionary_id, dictionary_spec))
                    ids.append(f"{provider_id}: {dictionary_id}")

            metafunc.parametrize("provider,dictionary_id,spec", params, ids=ids)


class TestProvider:
    def test_id_not_empty(self, klass: type[Provider]):
        id = klass.id()
        assert isinstance(id, str) and id != ""

    def test_name_not_empty(self, klass: type[Provider]):
        name = klass.name()
        assert isinstance(name, str) and name != ""

    def test_supported_dictionaries_valid(self, klass: type[Provider]):
        dictionaries = klass.supported_dictionaries()
        assert isinstance(dictionaries, dict) and dictionaries != {}
        for dictionary_id, dictionary_info in dictionaries.items():
            assert isinstance(dictionary_id, str) and dictionary_id != ""
            assert isinstance(dictionary_info, DictionaryInfo)
            assert isinstance(dictionary_info.name, str) and dictionary_info.name != ""
            assert dictionary_info.icon is None or isinstance(dictionary_info.icon, str) and dictionary_info.icon != ""

    def test_icon_valid(self, klass: type[Provider]):
        icon = klass.icon()
        assert icon is None or isinstance(icon, str) and icon != ""

    def test_fetch_definition(self, provider: Provider, dictionary_id: str, spec: dict[str, Any]):
        print(spec)

    @pytest.mark.generatetestdata
    def test_generate_test_cases(self, request: FixtureRequest, pytestconfig: Config, monkeypatch: MonkeyPatch):
        """
        When saving definitions into JSON files, the generator will only save the file if it doesn't exist.
        This is to prevent overwriting the correct definition when generating test data after a problematic change.

        For the cached response data, the generator will always remove the old ones and save the new ones.
        """

        original_request = requests.sessions.Session.request

        provider_id: str = pytestconfig.getoption("generate_test_data")
        for (provider, dictionary_id, spec) in _build_test_cases(provider_id, pytestconfig):
            # Create the dictionary directory if it doesn't exist
            dictionary_dir = request.path.parent.joinpath(provider_id, dictionary_id)
            if not dictionary_dir.exists():
                dictionary_dir.mkdir(parents=True, exist_ok=True)

            last_request_time = time.perf_counter() - spec["interval"]
            words = spec.get("words", [])
            for item in words:
                # Parse word specs
                expected_error: type[Exception] | None = None
                expected_error_attrs: dict[str, Any] | None = None
                if isinstance(item, str):
                    # short syntax
                    word: str = item
                elif isinstance(item, dict):
                    # long syntax
                    word = item["word"]
                    error_spec: dict[str, Any] | None = item.get("error")
                    if error_spec is not None:
                        error_type = cast(type | None, locate(f"omnidict.provider.common.{error_spec["type"]}"))
                        if error_type is not None and issubclass(error_type, Exception):
                            expected_error = error_type
                            expected_error_attrs = error_spec.get("attributes")
                else:
                    raise TypeError(f"Invalid dictionaries.*.words item: {item}")

                # Sleep to make sure the interval between requests is respected.
                if time.perf_counter() - last_request_time < spec["interval"]:
                    time.sleep(spec["interval"] - (time.perf_counter() - last_request_time))

                recorded_responses: list[requests.Response] = []
                definition: Definition | None = None
                with monkeypatch.context() as m:
                    if spec["mode"] != "online":
                        def record_requests(*args, **kwargs):
                            response = original_request(*args, **kwargs)
                            recorded_responses.append(response)
                            return response

                        m.setattr(requests.sessions.Session, "request", record_requests)

                    try:
                        last_request_time = time.perf_counter()
                        definition = provider.fetch_definition(dictionary_id, word, download_audio=True)
                    except expected_error as e:
                        print(f"Failed to fetch definition for {word}: {e}")

                # Write the definition to json file if not exists
                word_json = dictionary_dir.joinpath(f"{word}.json")
                if definition is not None and not word_json.exists():
                    with open(word_json, "wb") as json_file:
                        json = orjson.dumps(definition, default=_bytes_encode,
                                            option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_INDENT_2)
                        json_file.write(json)
