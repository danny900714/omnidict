import base64
import os
import time
import warnings
from pydoc import locate
from typing import Any, cast
from urllib.parse import urlsplit

import orjson
import pytest
import requests.sessions
from pytest import Metafunc, Config, FixtureRequest, MonkeyPatch
from requests import Response

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


def _parse_word_spec(word_spec: Any) -> tuple[str, type[type[Exception]], dict[str, Any] | None]:
    # Parse word specs
    expected_error: tuple[type[Exception]] = tuple()
    expected_error_attrs: dict[str, Any] | None = None
    if isinstance(word_spec, str):
        # short syntax
        word: str = word_spec
    elif isinstance(word_spec, dict):
        # long syntax
        word = word_spec["word"]
        error_spec: dict[str, Any] | None = word_spec.get("error")
        if error_spec is not None:
            error_type = cast(type | None, locate(f"omnidict.provider.common.{error_spec["type"]}"))
            if error_type is not None and issubclass(error_type, Exception):
                expected_error = (error_type,)
                expected_error_attrs = error_spec.get("attributes")
    else:
        raise TypeError(f"Invalid dictionaries.*.words item: {word_spec}")

    return word, expected_error, expected_error_attrs


def _bytes_encode(obj: Any) -> Any:
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Cannot serialize object of {type(obj)}")


def pytest_generate_tests(metafunc: Metafunc):
    if metafunc.cls and issubclass(metafunc.cls, TestProvider):
        if metafunc.fixturenames == ["klass"]:
            metafunc.parametrize("klass", metafunc.config.stash[providers_key].values())
        elif metafunc.fixturenames == ["provider", "dictionary_id", "spec", "monkeypatch", "request"]:
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

    def test_fetch_definition(self, provider: Provider, dictionary_id: str, spec: dict[str, Any],
                              monkeypatch: MonkeyPatch, request: FixtureRequest):
        use_local_cache = spec["mode"] == "local" or spec["mode"] == "local-unless-ci" and os.getenv("CI") is None
        dictionary_dir = request.path.parent.joinpath(provider.id(), dictionary_id)
        last_request_time = time.perf_counter() - spec["interval"]

        with monkeypatch.context() as m:
            # Use local cache when mode is local or local-unless-ci and not running in CI environment
            if use_local_cache:
                def return_local_cache(*args, **kwargs):
                    url = args[2]
                    split_result = urlsplit(url)
                    data_dir = request.path.parent.joinpath(provider.id(), "data")
                    response_path = data_dir.joinpath(split_result.hostname, *split_result.path.split("/"))
                    if response_path.exists():
                        with open(response_path, "rb") as response_file:
                            response_content = response_file.read()
                            response = Response()
                            response.status_code = 200
                            response._content = response_content
                            response.url = url
                            return response
                    raise ConnectionError(f"No local cache found for {url}")

                m.setattr(requests.sessions.Session, "request", return_local_cache)

            words = spec.get("words", [])
            for item in words:
                # Parse word specs
                word, expected_error, expected_error_attrs = _parse_word_spec(item)

                # Sleep to make sure the interval between requests is respected.
                # Only apply when not using local caches
                if not use_local_cache and time.perf_counter() - last_request_time < spec["interval"]:
                    time.sleep(spec["interval"] - (time.perf_counter() - last_request_time))

                def check_error_attrs(e: Exception):
                    if expected_error_attrs is not None:
                        for expected_attr_name, expected_attr_value in expected_error_attrs.items():
                            if getattr(e, expected_attr_name) != expected_attr_value:
                                return False
                    return True

                last_request_time = time.perf_counter()
                if len(expected_error) == 0:
                    definition = provider.fetch_definition(dictionary_id, word, download_audio=True)

                    # Assert definition
                    actual_definition_dict = orjson.loads(orjson.dumps(definition, default=_bytes_encode))
                    with open(dictionary_dir.joinpath(f"{word}.json"), "rb") as json_file:
                        expected_definition_dict = orjson.loads(json_file.read())
                    assert actual_definition_dict == expected_definition_dict
                else:
                    with pytest.raises(expected_error, check=check_error_attrs):
                        provider.fetch_definition(dictionary_id, word, download_audio=True)

    @pytest.mark.generatetestdata
    def test_generate_test_cases(self, request: FixtureRequest, pytestconfig: Config, monkeypatch: MonkeyPatch):
        """
        When saving definitions into JSON files, the generator will only save the file if it doesn't exist.
        This is to prevent overwriting the correct definition when generating test data after a problematic change.

        For the cached response data, the generator will always overrite the old ones.
        """

        original_request = requests.sessions.Session.request

        provider_id: str = pytestconfig.getoption("generate_test_data")
        for (provider, dictionary_id, spec) in _build_test_cases(provider_id, pytestconfig):
            # Create the dictionary directory if it doesn't exist
            dictionary_dir = request.path.parent.joinpath(provider_id, dictionary_id)
            if not dictionary_dir.exists():
                dictionary_dir.mkdir(parents=True, exist_ok=True)

            # Create data directory if it doesn't exist and request mode is not online (requires saving local cache).
            data_dir = request.path.parent.joinpath(provider_id, "data")
            if spec["mode"] != "online" and not data_dir.exists():
                data_dir.mkdir(parents=True, exist_ok=True)

            last_request_time = time.perf_counter() - spec["interval"]
            words = spec.get("words", [])
            for item in words:
                # Parse word specs
                word, expected_error, expected_error_attrs = _parse_word_spec(item)

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
                        # Try to catch error as the spec specified. If the error mismatches, fire a warning and not saving the test data.
                        if expected_error_attrs is not None:
                            attr_mismatch = False
                            for expected_attr_name, expected_attr_value in expected_error_attrs.items():
                                actual_attr_value = getattr(e, expected_attr_name)
                                if actual_attr_value != expected_attr_value:
                                    warnings.warn(
                                        f"[{dictionary_id}] ({word}) Expected error attribute {expected_attr_name} with value {expected_attr_value}, but got {actual_attr_value}")
                                    attr_mismatch = True

                            if attr_mismatch:
                                continue
                    except Exception as e:
                        # Catch all other errors and skip saving data for this word
                        warnings.warn(
                            f"[{dictionary_id}] ({word}) Unexpected error. The test data is not saved for that word\n{e}")
                        continue

                # Write the definition to json file if not exists
                word_json = dictionary_dir.joinpath(f"{word}.json")
                if definition is not None and not word_json.exists():
                    with open(word_json, "wb") as json_file:
                        json = orjson.dumps(definition, default=_bytes_encode,
                                            option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_INDENT_2)
                        json_file.write(json)

                # Write the recorded responses to data directory
                for response in recorded_responses:
                    split_url = urlsplit(response.url)

                    # Create host directory if not exists
                    if split_url.hostname is None:
                        continue
                    host_directory = data_dir.joinpath(cast(str, split_url.hostname))
                    if not host_directory.exists():
                        host_directory.mkdir(parents=True, exist_ok=True)

                    # Recreate the directory structure based on URL path
                    path_dir = host_directory
                    path_parts = split_url.path.split("/")
                    for i, part in enumerate(path_parts):
                        if i < len(path_parts) - 1:
                            path_dir = path_dir.joinpath(part)
                    if not path_dir.exists():
                        path_dir.mkdir(parents=True, exist_ok=True)

                    # Write the response to file if response has body
                    if response.content:
                        response_path = path_dir.joinpath(path_parts[-1])
                        with open(response_path, "wb") as response_file:
                            response_file.write(response.content)
