from typing import Optional
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from requests import Session

from . import DefinitionParseError
from .browser import header_generator
from .dictionary import Definition, Entry, Sense, Example, DefinitionNotFoundError, DefinitionRedirectedError


def _parse_supported_target_languages(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    bilingual_list = soup.select_one("amp-state#stateSidebarDictBi ~ ul")
    semi_bilingual_list = soup.select_one("amp-state#stateSidebarDictBi ~ div:last-child")
    if not bilingual_list or not semi_bilingual_list:
        raise DefinitionParseError("Failed to parse supported target languages")

    target_languages = {}
    for list_element in [bilingual_list, semi_bilingual_list]:
        buttons = list_element.select('span[role="button"].hp')
        for button in buttons:
            code = button.attrs["data-dictcode"]
            if not isinstance(code, str):
                raise DefinitionParseError("Failed to parse supported target languages")
            name = button.text.removeprefix("English–")
            target_languages[code] = name

    return target_languages


def _parse_definition(dict_code: str, html: str) -> Definition:
    # Current implementation only supports english-chinese dictionary families, other dictionary support is welcome
    supported_dict_codes = ["english-chinese-simplified", "english-chinese-traditional"]
    if dict_code not in supported_dict_codes:
        raise NotImplementedError(f"Dictionary code {dict_code} is not supported")

    soup = BeautifulSoup(html, "html.parser")

    word = soup.select_one("h1 b")
    if word is None:
        raise DefinitionParseError("Failed to parse word")
    word = word.get_text()

    # Limit the first entry to exclude prefix and sufix
    entry_bodies = soup.select(".di-body > .entry:first-child .entry-body__el")
    entries: list[Entry] = []
    for entry in entry_bodies:
        # Parse part of speech
        pos_element = entry.select_one(".pos-header > .posgram")
        pos = pos_element.get_text() if pos_element is not None else None

        # Parse entry usage, which will be appended to features of all senses
        usage_element = entry.select_one(".pos-header > span.lab > span.usage")
        entry_features = usage_element.get_text() if usage_element is not None else None

        # Parse UK and US phonemic transcriptions
        phonemic_transcriptions: Optional[dict[str, str]] = {}
        pt_uk_elem = entry.select_one("span.uk.dpron-i > span.pron.dpron")
        if pt_uk_elem is not None:
            phonemic_transcriptions["UK"] = pt_uk_elem.get_text()
        pt_us_elem = entry.select_one("span.us.dpron-i > span.pron.dpron")
        if pt_us_elem is not None:
            phonemic_transcriptions["US"] = pt_us_elem.get_text()
        if phonemic_transcriptions == {}:
            phonemic_transcriptions = None

        # to exclude phrase block
        def_blocks = entry.select(".sense-body > .def-block")
        senses: list[Sense] = []
        for def_block in def_blocks:
            # Parse features
            features: Optional[str] = None
            def_info = def_block.select_one("span.def-info")
            if def_info is not None:
                epp = def_info.select_one("span.epp-xref")
                if epp is not None:
                    epp.decompose()
                features = def_info.get_text().strip()
                features = features if features != "" else None

            # Append entry features to features of all senses
            if entry_features is not None:
                if features is not None:
                    features += f" {entry_features}"
                else:
                    features = entry_features

            # Parse definition (required)
            def_element = def_block.select_one("div.def")
            if def_element is None:
                raise DefinitionParseError("Failed to parse definition")
            definition = def_element.get_text()

            # Parse translation
            translation_element = def_block.select_one("span.trans")
            translation = translation_element.get_text() if translation_element is not None else None

            # Parse examples
            examples: list[Example] = []
            example_elements = def_block.select(".examp")
            for example_element in example_elements:
                sentence_element = example_element.select_one("span.eg")
                if sentence_element is not None:
                    sentence = sentence_element.get_text()

                    example_translation_element = example_element.select_one("span.trans")
                    example_translation = example_translation_element.get_text() if example_translation_element is not None else None

                    example = Example(sentence, translation=example_translation)
                    examples.append(example)

            # Create sense object and append it to list
            sense = Sense(definition, features=features, translation=translation, examples=examples)
            senses.append(sense)

        # Create entry object and append it to list if senses is not empty
        if len(senses) > 0:
            entry = Entry(senses, part_of_speech=pos, phonemic_transcriptions=phonemic_transcriptions)
            entries.append(entry)

    # Create the definition object
    return Definition(word, entries)


class Client:
    def __init__(self):
        self.session = Session()
        self.session.headers.update(header_generator.generate())

    def __del__(self):
        self.session.close()

    def fetch_supported_target_languages(self) -> dict[str, str]:
        response = self.session.get("https://dictionary.cambridge.org/")
        return _parse_supported_target_languages(response.text)

    def fetch_definition(self, dict_code: str, vocabulary: str) -> Definition:
        url = f"https://dictionary.cambridge.org/dictionary/{dict_code}/{vocabulary}"

        # Disable redirection because Cambridge Dictionary will redirect to phrase that contains the vocabulary if the vocabulary doesn't have a definition (letter -> air letter)
        response = self.session.get(url, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("location")
            if location is not None:
                location_url = urlsplit(location)
                if location_url.path == f"/dictionary/{dict_code}/":
                    raise DefinitionNotFoundError(f"No definition found for {vocabulary}")
                elif location_url.path.startswith(
                        f"/dictionary/{dict_code}/") and location_url.query == f"q={vocabulary}":
                    redirected_word = location_url.path.split("/")[-1]

                    # Check if the redirected word is the lowercase of the queried word due to wierd redirection made by Cambridge Dictionary (CPU -> cpu)
                    if vocabulary.lower() == redirected_word:
                        return self.fetch_definition(dict_code, redirected_word)

                    raise DefinitionRedirectedError(redirected_word)

            raise RuntimeError(f"Unexpected redirect response: {vars(response.headers)}")

        response.raise_for_status()

        return _parse_definition(dict_code, response.text)
