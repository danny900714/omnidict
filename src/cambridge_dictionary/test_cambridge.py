import json

import jsonpickle

from .cambridge import _parse_supported_target_languages, _parse_definition

jsonpickle.set_encoder_options("json", ensure_ascii=False)


def test_parse_supported_target_languages():
    with open("testdata/dictionary.cambridge.org/index.html") as f:
        html = f.read()
        target_languages = _parse_supported_target_languages(html)

        with open("src/cambridge_dictionary/user_files/target_languages.json", "r") as target_languages_json:
            assert target_languages == json.load(target_languages_json)


def test_parse_definition():
    print()
    with open("testdata/dictionary.cambridge.org/dictionary/english-chinese-traditional/flash.html") as html_file:
        html = html_file.read()
        definition = _parse_definition(html)

        # Store json for the given file
        # definition_json = jsonpickle.encode(definition, unpicklable=False, indent=2)
        # with open("testdata/dictionary.cambridge.org/dictionary/english-chinese-traditional/flash.json",
        #           "w") as json_file:
        #     json_file.write(definition_json)
