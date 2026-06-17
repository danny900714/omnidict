from enum import Enum
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from requests import Session

from .common import (
    Definition,
    DefinitionNotFoundError,
    DefinitionParseError,
    DefinitionRedirectedError,
    DictionaryInfo,
    Entry,
    Example,
    Pronunciation,
    Provider,
    Sense,
)

ORIGIN = "https://dictionary.cambridge.org"


class _DiBodyChildType(Enum):
    ENTRY = "entry"
    IDIOM = "idiom"
    PHRASE = "phrase"
    PHRASAL_VERB = "phrasal verb"


class CambridgeDictionaryProvider(Provider):
    _ID = "cambridge-dictionary"
    _NAME = "Cambridge Dictionary"
    _ICON = str(
        Path(__file__)
        .parent.parent.joinpath("assets", "icons", "cambridge-dictionary.svg")
        .absolute()
    )
    _DICTIONARIES = {
        "english-chinese-simplified": DictionaryInfo(
            "Cambridge English–Chinese (Simplified) Dictionary"
        ),
        "english-chinese-traditional": DictionaryInfo(
            "Cambridge English-Chinese (Traditional) Dictionary"
        ),
    }

    def __init__(self):
        self.session = Session()
        self.session.headers.update(self.browser_headers())

    def __del__(self):
        self.session.close()

    def fetch_definition(
        self, dictionary_id: str, word: str, *, download_audio: bool
    ) -> Definition:
        url = f"{ORIGIN}/dictionary/{dictionary_id}/{word.replace(' ', '-')}"  # Cambridge Dictionary replaces spaces with hyphens in URL

        # Disable redirection because Cambridge Dictionary will redirect to phrase that contains the vocabulary if the vocabulary doesn't have a definition (letter -> air letter)
        response = self.session.get(url, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("location")
            if location is not None:
                location_url = urlsplit(location)
                if location_url.path == f"/dictionary/{dictionary_id}/":
                    raise DefinitionNotFoundError(f"No definition found for {word}")
                elif (
                    location_url.path.startswith(f"/dictionary/{dictionary_id}/")
                    and location_url.query == f"q={word}"
                ):
                    redirected_word = location_url.path.split("/")[-1]

                    # Check if the redirected word is the lowercase of the queried word due to weird redirection made by Cambridge Dictionary (CPU -> cpu)
                    if word.lower() == redirected_word:
                        return self.fetch_definition(
                            dictionary_id,
                            redirected_word,
                            download_audio=download_audio,
                        )

                    raise DefinitionRedirectedError(redirected_word)

            raise RuntimeError(
                f"Unexpected redirect response: {vars(response.headers)}"
            )

        response.raise_for_status()

        if dictionary_id in [
            "english-chinese-simplified",
            "english-chinese-traditional",
        ]:
            return self._parse_chinese_definition(response.text, download_audio)
        else:
            raise DefinitionParseError(f"Unsupported dictionary id: {dictionary_id}")

    def _download_file(self, url: str) -> bytes:
        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    def _parse_chinese_definition(self, html: str, download_audio: bool) -> Definition:
        soup = BeautifulSoup(html, "html.parser")

        # ASSUMPTION: the basename of the url path is unique within the webpage
        audio_files: dict[str, bytes] = {}

        # The first selector is to select regular entry and phrasal verb
        # The second selector is to select the inner idiom block
        # The third selector is to select phrase block
        entry_blocks = soup.select(
            ".di-body :is(.entry .entry-body__el, .idiom-block .idiom-block, .phrase-di-block)"
        )
        entries: list[Entry] = []
        for entry_block in entry_blocks:
            # Parse headword of entry
            headword_element = entry_block.select_one(".headword")
            headword = (
                headword_element.get_text() if headword_element is not None else None
            )
            if headword is None or headword == "":
                raise DefinitionParseError("Failed to parse entry headword")

            # Parse part of speech.
            # When selecting entry pos, we select .posgram because there's a possible child (span.gram.dgram) contains the additional code.
            # When selecting pos for other types, use :first-child to select the direct pos since phrasal verb also has another .pos.dpos for verb (see fuck around).
            pos_element = entry_block.select_one(
                ":is(.pos-header > .posgram, span.di-info span.pos.dpos:first-child)"
            )
            pos = pos_element.get_text() if pos_element is not None else None

            # Parse entry usage, which will be appended to features of all senses
            # The first selector applies to entry.
            #   The :not(.pv-block *) is used to exclude phrasal verb because it appends the verb usage, which is not what we want.
            # The second selector applies to idiom and phrase.
            usage_element = entry_block.select_one(
                ":is(.pos-header > span.lab > span.usage:not(.pv-block *), span.di-info > span.lab > span.usage)"
            )
            entry_features = (
                usage_element.get_text() if usage_element is not None else None
            )

            # Parse pronunciations
            # Select .pos-header > span.dpron-i to exclude plural pronunciation (see man).
            # Apply :not(.pv-block *) to exclude phrasal verb pronunciations because they are the pronunciations of the verb.
            pronunciation_spans = entry_block.select(
                ".pos-header > span.dpron-i:not(.pv-block *)"
            )
            pronunciations: list[Pronunciation] = []
            for pronunciation_span in pronunciation_spans:
                # Parse region
                region_span = pronunciation_span.select_one("span.region")
                region = (
                    region_span.get_text().upper() if region_span is not None else None
                )

                # Parse audio URL
                audio_source = (
                    pronunciation_span.select_one(".daud audio source")
                    if download_audio
                    else None
                )
                audio_source_src = (
                    cast(str, audio_source.get("src"))
                    if audio_source is not None
                    else None
                )
                audio_url = (
                    urljoin(ORIGIN, audio_source_src)
                    if audio_source_src is not None
                    else None
                )

                # Parse phonemic transcription
                transcription_span = pronunciation_span.select_one("span.pron.dpron")
                transcription = (
                    transcription_span.get_text()
                    if transcription_span is not None
                    else None
                )

                # Download audio file if audio file not in audio_files map
                audio_file_name: str | None = None
                if audio_url is not None:
                    audio_file_name: str = self._url_to_filename(audio_url)
                    if audio_file_name not in audio_files:
                        try:
                            audio = self._download_file(audio_url)
                            audio_files[audio_file_name] = audio
                        except Exception as e:
                            print(f"Failed to download audio from {audio_url}:\n{e}")

                pronunciation = Pronunciation(
                    region=region,
                    audio_file_name=audio_file_name,
                    phonemic_transcription=transcription,
                )
                pronunciations.append(pronunciation)

            # Selects sense def-block
            # The first selector is to match entry, phrasal verb, and idiom
            # The second selector is to match phrase
            # The reason why not directly select .def-block is to exclude phrase block, which has .phrase-block .def-vlock
            def_blocks = entry_block.select(
                ":is(.sense-body, span.phrase-di-body) > .def-block"
            )
            senses: list[Sense] = []
            for def_block in def_blocks:
                sense = self._parse_chinese_definition_def_block(
                    def_block, entry_features
                )
                senses.append(sense)

            # Create entry object and append it to list if senses is not empty
            if len(senses) > 0:
                entry = Entry(
                    headword,
                    senses,
                    part_of_speech=pos,
                    pronunciations=pronunciations
                    if len(pronunciation_spans) > 0
                    else None,
                )
                entries.append(entry)

        if len(entries) == 0:
            raise DefinitionParseError("Failed to parse definition")

        # Create the definition object
        return Definition(entries, audio_files=audio_files if audio_files else None)

    @staticmethod
    def _parse_chinese_definition_def_block(
        def_block: Tag, entry_features: str | None
    ) -> Sense:
        # Parse features
        features: str | None = None
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

            features = (
                def_info.get_text().strip().replace("\n", "")
            )  # Remove all \n that comes before divider
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
        translation = (
            translation_element.get_text() if translation_element is not None else None
        )

        # Parse examples
        examples: list[Example] = []
        example_elements = def_block.select(".examp")
        for example_element in example_elements:
            sentence_element = example_element.select_one("span.eg")
            if sentence_element is not None:
                sentence = sentence_element.get_text()

                example_translation_element = example_element.select_one("span.trans")
                example_translation = (
                    example_translation_element.get_text()
                    if example_translation_element is not None
                    else None
                )

                example = Example(sentence, translation=example_translation)
                examples.append(example)

        return Sense(
            definition,
            features=features,
            translation=translation,
            examples=examples,
        )

    @staticmethod
    def _url_to_filename(url: str) -> str:
        return Path(unquote(urlsplit(url).path)).name
