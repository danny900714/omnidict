import re
from pathlib import Path
from typing import ClassVar, cast
from urllib.parse import unquote, urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from requests import Session
from requests.exceptions import RequestException

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


class CambridgeDictionaryProvider(Provider):
    _ID = "cambridge-dictionary"
    _NAME = "Cambridge Dictionary"
    _ICON = str(
        Path(__file__)
        .parent.parent.joinpath("assets", "icons", "cambridge-dictionary.svg")
        .absolute()
    )
    _DICTIONARIES: ClassVar[dict[str, DictionaryInfo]] = {
        "english-chinese-simplified": DictionaryInfo(
            "Cambridge English–Chinese (Simplified) Dictionary"
        ),
        "english-chinese-traditional": DictionaryInfo(
            "Cambridge English-Chinese (Traditional) Dictionary"
        ),
        "english-advanced-learner": DictionaryInfo(
            "Cambridge Advanced Learner's Dictionary & Thesaurus"
        ),
        "english-academic-content": DictionaryInfo(
            "Cambridge Academic Content Dictionary"
        ),
        "english-business-english": DictionaryInfo(
            "Cambridge Business English Dictionary"
        ),
    }

    _RESPONSE_URL_PATH_PATTERN = re.compile(r"^/dictionary/(?P<dataset>\S*)/.*$")

    _ENGLISH_DICTIONARY_DATA_ID: ClassVar[dict[str, str]] = {
        "english-advanced-learner": "cald4",
        "english-academic-content": "cacd",
        "english-business-english": "cbed",
    }
    _PLACEHOLDERS: ClassVar[set[str]] = {
        "someone",
        "somebody",
        "sb",
        "something",
        "sth",
        "anything",
        "somewhere",
        "someone's",
        "somebody's",
        "your",
        "be",
    }

    def __init__(self):
        self.session = Session()
        self.session.headers.update(self.browser_headers())

    def __del__(self):
        self.session.close()

    def fetch_definition(
        self, dictionary_id: str, term: str, *, download_audio: bool
    ) -> Definition:
        query = urlencode({
            "datasetsearch": self._get_dataset(dictionary_id),
            "q": term,
        })
        search_url = f"{ORIGIN}/search/direct/?{query}"
        return self._fetch_definition(
            dictionary_id, term, search_url, download_audio=download_audio
        )

    def _fetch_definition(
        self, dictionary_id: str, search_term: str, url: str, *, download_audio: bool
    ) -> Definition:
        response = self.session.get(url)
        self.logger.debug(f'"{search_term}" queried. Response URL: {response.url}')
        response.raise_for_status()

        dataset = self._get_dataset(dictionary_id)
        url = urlsplit(response.url)
        if url.path == f"/spellcheck/{dataset}/":
            raise DefinitionNotFoundError(f"No definition found for {search_term}")

        match = self._RESPONSE_URL_PATH_PATTERN.match(url.path)
        response_dataset: str | None = match.group("dataset") if match else None
        self.logger.debug(f"Response dataset: {response_dataset}")

        if response_dataset is None:
            raise DefinitionParseError(f"Unexpected response URL: {response.url}")
        elif response_dataset != dataset:
            # TODO: handle cross dictionary redirect
            raise DefinitionNotFoundError(f"No definition found for {search_term}")
        elif response_dataset in [
            "english-chinese-simplified",
            "english-chinese-traditional",
        ]:
            return self._parse_chinese_definition(
                dictionary_id, search_term, response.text, download_audio=download_audio
            )
        elif response_dataset == "english":
            return self._parse_english_definition(
                dictionary_id, search_term, response.text, download_audio=download_audio
            )
        else:
            raise DefinitionParseError(f"Unsupported dictionary id: {response_dataset}")

    def _parse_english_definition(
        self, dictionary_id: str, search_term: str, html: str, *, download_audio: bool
    ) -> Definition:
        soup = BeautifulSoup(html, "html.parser")

        data_id = self._ENGLISH_DICTIONARY_DATA_ID.get(dictionary_id)
        self.logger.debug(f"English dictionary data-id: {data_id}")
        if data_id is None:
            raise DefinitionParseError(f"Unsupported dictionary id: {dictionary_id}")

        dictionaries = soup.select(".dictionary")
        for d in dictionaries:
            if d.get("data-id") == data_id:
                dictionary = d
                break
        else:
            if len(dictionaries) > 0:
                alt_data_id = cast(str | None, dictionaries[0].get("data-id"))
                for dict_id, data_id in self._ENGLISH_DICTIONARY_DATA_ID.items():
                    if alt_data_id == data_id:
                        raise DefinitionRedirectedError(search_term, dict_id)
            raise DefinitionParseError(
                f"Failed to parse dictionary's data-id from English dictionary:\n{dictionaries}"
            )

        return self._parse_dictionary_block(dictionary, download_audio=download_audio)

    def _parse_chinese_definition(
        self, dictionary_id: str, search_term: str, html: str, *, download_audio: bool
    ) -> Definition:
        soup = BeautifulSoup(html, "html.parser")

        # If the search term has multiple words, we assume it to be an embedded phrase.
        # We then check whether the search term matches any headword of the embedded phrase block.
        if search_term.count(" ", 0, -1) > 0:
            entries: list[Entry] = []

            # Parse embedded phrase block
            phrase_blocks = soup.select(".dsense > .sense-body > .phrase-block")
            for phrase_block in phrase_blocks:
                # Parse embedded phrase title
                phrase_title_element = phrase_block.select_one(
                    ".phrase-head > span.phrase-title > b"
                )
                phrase_title = (
                    phrase_title_element.get_text()
                    if phrase_title_element is not None
                    else None
                )

                if phrase_title and self._is_phrase_title_match(
                    search_term, phrase_title
                ):
                    self.logger.debug(
                        'Search term "%s" matches phrase title "%s"',
                        search_term,
                        phrase_title,
                    )

                    # Follow the see more button if it exists to go to the dedicated page for embedded phrase
                    see_more_button = phrase_block.select_one("span.dbtn > a.hbtn.bh")
                    phrase_page_url = cast(
                        str | None,
                        see_more_button.get("href") if see_more_button else None,
                    )
                    if phrase_page_url:
                        self.logger.debug(
                            f'Found "See more" button for phrase "{phrase_title}", url: {phrase_page_url}'
                        )

                        # For embedded phrase block with a "See more" button,
                        # we can only fetch the definition for the first phrase that matches
                        return self._fetch_definition(
                            dictionary_id,
                            search_term,
                            f"{ORIGIN}{phrase_page_url}",
                            download_audio=download_audio,
                        )
                    else:
                        # Parse phrase block
                        def_block = phrase_block.select_one(".phrase-body > .def-block")
                        if def_block is None:
                            raise DefinitionParseError(
                                f'Cannot parse embedded phrase def-block of "{phrase_title}".\nPhrase block:\n{phrase_block}'
                            )

                        sense = self._parse_def_block(def_block)
                        entry = Entry(phrase_title, [sense], part_of_speech="phrase")
                        entries.append(entry)

            # If the search term matches any embedded phrase block not having a "See more" button, return the entries parse from embedded phrase blocks
            if len(entries) > 0:
                return Definition(entries)

        return self._parse_dictionary_block(soup, download_audio=download_audio)

    def _parse_dictionary_block(
        self, dictionary_block: Tag, *, download_audio: bool
    ) -> Definition:
        # ASSUMPTION: the basename of the url path is unique within the webpage
        audio_files: dict[str, bytes] = {}
        entries: list[Entry] = []

        # The search term only contains a single word or doesn't match any embedded phrase block, we then parse the definition from the main entry blocks.
        # The first selector is to select regular entry and phrasal verb
        # The second selector is to select the inner idiom block
        # The third selector is to select phrase block
        entry_blocks = dictionary_block.select(
            ".di-body :is(.entry .entry-body__el, .idiom-block .idiom-block, .phrase-di-block)"
        )
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
            # Prepend :scope to exclude run-on pronunciations (see man: manliness in Cambridge Academic Content Dictionary)
            # Select .pos-header > span.dpron-i to exclude plural pronunciation (see man).
            # Apply :not(.pv-block *) to exclude phrasal verb pronunciations because they are the pronunciations of the verb.
            pronunciation_spans = entry_block.select(
                ":scope > .pos-header > span.dpron-i:not(.pv-block *)"
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
                        except RequestException as e:
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
                sense = self._parse_def_block(def_block, entry_features)
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
    def _parse_def_block(def_block: Tag, entry_features: str | None = None) -> Sense:
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

    def _is_phrase_title_match(self, search_term: str, phrase_title: str) -> bool:
        normalized_search_term = search_term.lower().strip()
        normalized_phrase_title = phrase_title.lower().strip()

        if normalized_search_term == normalized_phrase_title:
            return True

        # Interpret "-" as word divider and "," as slash
        normalized_search_term = normalized_search_term.replace("-", " ").replace(
            ", ", "/"
        )
        normalized_phrase_title = normalized_phrase_title.replace("-", " ").replace(
            ", ", "/"
        )

        # Split phrase by space and get the index of parenthesized words
        search_term_words, parenthesized_st_idx = self._split_phrase(
            normalized_search_term
        )
        phrase_title_words, parenthesized_pt_idx = self._split_phrase(
            normalized_phrase_title
        )

        self.logger.debug(
            f"Search term words: {search_term_words}, parenthesized indexes: {parenthesized_st_idx}"
        )
        self.logger.debug(
            f"Phrase title words: {phrase_title_words}, parenthesized indexes: {parenthesized_pt_idx}"
        )

        sti = 0
        pti = 0

        # Only traverse the search term to include all phrases containing the search term
        while sti < len(search_term_words):
            st_variants = search_term_words[sti].split("/")
            pt_variants = phrase_title_words[pti].split("/")

            # If one of the variants of search term and phrase title matches, then move to the next search term and phrase title
            if set(st_variants) & set(pt_variants):
                sti += 1
                pti += 1
            else:
                # If search term is placeholder or is parenthesized, then move to the next search term
                if (
                    set(st_variants) & CambridgeDictionaryProvider._PLACEHOLDERS
                    or sti in parenthesized_st_idx
                ):
                    sti += 1
                # If phrase title is placeholder or is parenthesized, then move to the next phrase title
                elif (
                    set(pt_variants) & CambridgeDictionaryProvider._PLACEHOLDERS
                    or pti in parenthesized_pt_idx
                ):
                    pti += 1
                # Search term and phrase title doesn't intersect, and both of them aren't placeholder or parenthesized
                else:
                    return False

        return True

    @staticmethod
    def _split_phrase(phrase: str) -> tuple[list[str], list[int]]:
        """Split phrase by space.

        Returns:
            A tuple containing a list of words and a list of parenthesized words' indexes.
        """

        words = []
        parenthesized_words_idx = []
        parenthesized = False
        word_start = 0
        for i in range(len(phrase)):
            if phrase[i] == "(":
                word_start += 1
                parenthesized = True
            elif phrase[i] == ")":
                # Add the current word to the parenthesized list
                parenthesized_words_idx.append(len(words))
                # Since the current word is added to the list, set parenthesized to False
                parenthesized = False

            if phrase[i] == " " or i == len(phrase) - 1:
                # Add 1 to the end index if i is the last index to prevent the last word from being stripped
                word_end = i + 1 if i == len(phrase) - 1 else i

                if parenthesized:
                    parenthesized_words_idx.append(len(words))
                # The current word contains ")" if parenthesized is False, and it is included in parenthesized words
                # Hence, the trailing ")" is stripped
                elif len(parenthesized_words_idx) > 0 and parenthesized_words_idx[
                    -1
                ] == len(words):
                    word_end -= 1

                words.append(phrase[word_start:word_end])
                word_start = i + 1

        return words, parenthesized_words_idx

    def _download_file(self, url: str) -> bytes:
        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    @staticmethod
    def _get_dataset(dictionary_id: str) -> str:
        if dictionary_id in (
            "english-advanced-learner",
            "english-academic-content",
            "english-business-english",
        ):
            return "english"
        return dictionary_id

    @staticmethod
    def _url_to_filename(url: str) -> str:
        return Path(unquote(urlsplit(url).path)).name
