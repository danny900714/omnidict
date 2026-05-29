import json
import os.path
from typing import Optional

import jsonpickle
import pytest
from requests import Session

from .browser import header_generator
from .cambridge import _parse_supported_target_languages, _parse_definition

jsonpickle.set_encoder_options("json", ensure_ascii=False)


@pytest.fixture(scope="module")
def requests_session():
    session = Session()
    session.headers.update(header_generator.generate())
    return session


@pytest.fixture
def definition_test_cases(requests_session):
    test_cases = {
        "english-chinese-traditional": [
            "flash",
            "slash",  # additional information inside features that makes it two lines long ((UK also oblique (stroke)))
            "record",  # features in part of speech ([ T ]); phrase block
            "fuck",  # features in .pos-header (offensive)
            "man", # suffix (-man)
            "reborn", # only phrase block in sense body (be reborn)
            "bug", # irreg-infls under phonemic transcription (-gg)
            "CPU", # .lab .usage inside div.def (abbreviation for), but this is the result of a redirected page
        ],
    }

    result: list[tuple[str, dict | str]] = []
    for dict_code, vocabularies in test_cases.items():
        for vocabulary in vocabularies:
            html: str
            definition: Optional[dict] = None
            html_path = f"testdata/dictionary.cambridge.org/dictionary/{dict_code}/{vocabulary}.html"
            json_path = html_path.replace(".html", ".json")

            if os.path.exists(html_path):
                with open(html_path) as html_file:
                    html = html_file.read()

                if os.path.exists(json_path):
                    with open(json_path) as json_file:
                        definition = json.load(json_file)
            else:
                url = f"https://dictionary.cambridge.org/dictionary/{dict_code}/{vocabulary}"
                response = requests_session.get(url)
                html = response.text
                with open(html_path, "w") as html_file:
                    html_file.write(html)

            if definition is None:
                result.append((html, json_path))
            else:
                result.append((html, definition))

    return result


def test_parse_supported_target_languages():
    with open("testdata/dictionary.cambridge.org/index.html") as f:
        html = f.read()
        target_languages = _parse_supported_target_languages(html)

        with open("src/cambridge_dictionary/user_files/target_languages.json", "r") as target_languages_json:
            assert target_languages == json.load(target_languages_json)


def test_parse_definition(definition_test_cases):
    for test_case in definition_test_cases:
        html, definition = test_case

        actual_definition = _parse_definition(html)
        if isinstance(definition, str):
            definition_json = jsonpickle.encode(actual_definition, unpicklable=False, indent=2)
            with open(definition, "w") as json_file:
                json_file.write(definition_json)
        else:
            assert json.loads(jsonpickle.encode(actual_definition, unpicklable=False)) == definition
