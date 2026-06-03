import json
import os.path
from pathlib import Path
from typing import Optional

import jsonpickle
import pytest
from browserforge.headers import HeaderGenerator
from requests import Session

from cambridge_dictionary.provider.cambridge import _parse_chinese_definition

jsonpickle.set_encoder_options("json", ensure_ascii=False)
header_generator = HeaderGenerator()


@pytest.fixture(scope="module")
def browser_headers():
    return header_generator.generate()


@pytest.fixture(scope="module")
def requests_session(browser_headers):
    session = Session()
    session.headers.update(browser_headers)
    return session


@pytest.fixture
def definition_test_cases(requests_session):
    test_cases = {
        "english-chinese-traditional": [
            "flash",
            "slash",  # additional information inside features that makes it two lines long ((UK also oblique (stroke)))
            "record",  # features in part of speech ([ T ]); phrase block
            "fuck",  # features in .pos-header (offensive)
            "man",  # suffix (-man)
            "reborn",  # only phrase block in sense body (be reborn)
            "bug",  # irreg-infls under phonemic transcription (-gg)
            "CPU",  # .lab .usage inside div.def (abbreviation for), but this is the result of a redirected page
            "corpus",  # .ddivide cause extra spaces inside features (MEDICAL   specialized)
        ],
        "english-chinese-simplified": [
            "flash",
        ],
    }

    result: list[tuple[str, str, dict | str]] = []
    for dict_code, vocabularies in test_cases.items():
        for vocabulary in vocabularies:
            html: str
            definition: Optional[dict] = None
            html_path = f"tests/data/dictionary.cambridge.org/dictionary/{dict_code}/{vocabulary}.html"
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

                if not Path(html_path).parent.exists():
                    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
                with open(html_path, "w") as html_file:
                    html_file.write(html)

            if definition is None:
                result.append((dict_code, html, json_path))
            else:
                result.append((dict_code, html, definition))

    return result


def test_parse_chinese_definition(definition_test_cases):
    for test_case in definition_test_cases:
        dict_code, html, definition = test_case

        actual_definition = _parse_chinese_definition(html)
        if isinstance(definition, str):
            definition_json = jsonpickle.encode(actual_definition, unpicklable=False, indent=2)
            with open(definition, "w") as json_file:
                json_file.write(definition_json)
        else:
            assert json.loads(jsonpickle.encode(actual_definition, unpicklable=False)) == definition
