import json

from .cambridge import _parse_supported_target_languages


def test_parse_supported_target_languages():
    print()
    with open("testdata/dictionary.cambridge.org/index.html") as f:
        html = f.read()
        target_languages = _parse_supported_target_languages(html)

        with open("src/cambridge_dictionary/user_files/target_languages.json", "r") as target_languages_json:
            assert target_languages == json.load(target_languages_json)
