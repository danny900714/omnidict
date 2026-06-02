from typing import Optional
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from requests import Session

from ..common import Dictionary
from ...browser import header_generator
from ...dictionary import Definition, Entry, DefinitionParseError, Sense, Example, DefinitionNotFoundError, \
    DefinitionRedirectedError


def _parse_definition(html: str) -> Definition:
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
                # Exclude experience level capsule
                epp = def_info.select_one("span.epp-xref")
                if epp is not None:
                    epp.decompose()

                # Exclude divider that will cause extra spaces
                divider = def_info.select_one(".ddivide")
                if divider is not None:
                    divider.decompose()

                features = def_info.get_text().strip().replace("\n", "")  # Remove all \n that comes before divider
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


class ChineseDictionary(Dictionary):
    def __init__(self, id: str, name: str):
        self._id = id
        self._name = name

        self.session = Session()
        self.session.headers.update(header_generator.generate())

    def id(self) -> str:
        return self._id

    def name(self) -> str:
        return self._name

    def fetch_definition(self, word: str) -> Definition:
        url = f"https://dictionary.cambridge.org/dictionary/{self.id()}/{word}"

        # Disable redirection because Cambridge Dictionary will redirect to phrase that contains the vocabulary if the vocabulary doesn't have a definition (letter -> air letter)
        response = self.session.get(url, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("location")
            if location is not None:
                location_url = urlsplit(location)
                if location_url.path == f"/dictionary/{self.id()}/":
                    raise DefinitionNotFoundError(f"No definition found for {word}")
                elif location_url.path.startswith(
                        f"/dictionary/{self.id()}/") and location_url.query == f"q={word}":
                    redirected_word = location_url.path.split("/")[-1]

                    # Check if the redirected word is the lowercase of the queried word due to wierd redirection made by Cambridge Dictionary (CPU -> cpu)
                    if word.lower() == redirected_word:
                        return self.fetch_definition(redirected_word)

                    raise DefinitionRedirectedError(redirected_word)

            raise RuntimeError(f"Unexpected redirect response: {vars(response.headers)}")

        response.raise_for_status()

        return _parse_definition(response.text)
