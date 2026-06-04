from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from anki.collection import Collection
from browserforge.headers import HeaderGenerator
from bs4 import BeautifulSoup

_header_generator = HeaderGenerator()


@dataclass
class Example:
    sentence: str
    translation: str | None = field(default_factory=None)


@dataclass
class Sense:
    definition: str
    features: str | None = field(default_factory=None)
    translation: str | None = field(default_factory=None)
    examples: list[Example] | None = field(default_factory=None)


@dataclass
class Pronunciation:
    region: str | None = field(default_factory=None)
    audio_file_name: str | None = field(default_factory=None)
    phonemic_transcription: str | None = field(default_factory=None)

    def __post_init__(self):
        if self.audio_file_name is None and self.phonemic_transcription is None:
            raise ValueError("At least one of audio_file_name and phonemic_transcription must be provided.")


@dataclass
class Entry:
    senses: list[Sense]
    pronunciations: list[Pronunciation] | None = field(default_factory=None)
    part_of_speech: str | None = field(default_factory=None)


@dataclass
class Definition:
    word: str
    entries: list[Entry]
    audio_files: dict[str, bytes] | None = field(default_factory=None)

    _saved_audio_files: dict[str, str] = field(default_factory=dict, init=False)

    @staticmethod
    @cache
    def _css():
        path = Path(__file__).parent.parent / "assets" / "definition.css"
        with open(path) as f:
            return f.read()

    def has_unsaved_audio_files(self) -> bool:
        return self.audio_files is not None and len(self._saved_audio_files) < len(self.audio_files)

    def save_audio_files(self, col: Collection):
        if self.has_unsaved_audio_files():
            for filename, data in self.audio_files.items():
                # Only save audio file if it hasn't been saved before
                if filename not in self._saved_audio_files:
                    self._saved_audio_files[filename] = col.media.write_data(filename, data)

    def render_html(self, *, include_audio: bool = False, include_phonemic_transcriptions: bool = True,
                    include_translations: bool = True,
                    include_examples: bool = False) -> str:
        soup = BeautifulSoup("", "html.parser")
        soup.append(soup.new_tag("style", string=Definition._css()))
        root = soup.new_tag("div", attrs={"class": "root"})
        soup.append(root)

        for entry in self.entries:
            header = soup.new_tag("div", attrs={"class": "header"})
            root.append(header)
            header.append(soup.new_tag("b", string=self.word))

            # Render pronunciations
            if entry.pronunciations is not None and (include_audio or include_phonemic_transcriptions):
                for pronunciation in entry.pronunciations:
                    pronunciation_span = soup.new_tag("span", attrs={"class": "pronunciation"})
                    header.append(pronunciation_span)

                    if pronunciation.region is not None:
                        pronunciation_span.append(
                            soup.new_tag("span", attrs={"class": "text-disabled"}, string=pronunciation.region))
                    if include_audio and pronunciation.audio_file_name is not None:
                        audio_fname = self._saved_audio_files.get(pronunciation.audio_file_name)
                        if audio_fname is not None:
                            pronunciation_span.append(
                                soup.new_tag("span", attrs={"class": "text-subtle"}, string=f"[sound:{audio_fname}]"))
                    if include_phonemic_transcriptions and pronunciation.phonemic_transcription is not None:
                        pronunciation_span.append(soup.new_tag("span", attrs={"class": "text-subtle"},
                                                               string=pronunciation.phonemic_transcription))

            # Render part of speech
            if entry.part_of_speech is not None:
                header.append(soup.new_tag("i", attrs={"class": "text-subtle"}, string=entry.part_of_speech))

            # Render senses list
            ol = soup.new_tag("ol")
            root.append(ol)
            for sense in entry.senses:
                li = soup.new_tag("li", string=sense.definition)
                ol.append(li)

                # Insert features before the definition
                if sense.features is not None:
                    features_span = soup.new_tag("span", attrs={"class": "text-subtle mr-3"}, string=sense.features)
                    li.insert(0, features_span)

                # Append translation after the definition
                if include_translations and sense.translation is not None:
                    li.append(soup.new_tag("br"))
                    li.append(soup.new_tag("span", attrs={"class": "text-blue"}, string=sense.translation))

                # Append the example list
                if include_examples and sense.examples is not None:
                    li.append(soup.new_tag("br"))
                    ul = soup.new_tag("ul")
                    li.append(ul)
                    for example in sense.examples:
                        li_example = soup.new_tag("li", string=example.sentence)
                        ul.append(li_example)
                        if include_translations and example.translation is not None:
                            li_example.append(soup.new_tag("br"))
                            li_example.append(
                                soup.new_tag("span", attrs={"class": "text-blue"}, string=example.translation))

            root.append(soup.new_tag("br"))

        soup.smooth()
        return str(soup)


class DefinitionNotFoundError(RuntimeError):
    """This error should be raised when a dictionary cannot find the definition for the given word.

    This error should only be raised when the dictionary doesn't have a definition for the queried word.
    For more general errors like malformed response or connection issues, please raise custom exceptions.
    """
    pass


class DefinitionParseError(RuntimeError):
    """This error should be raised when a dictionary gets the definition but unable to parse it."""
    pass


class DefinitionRedirectedError(RuntimeError):
    """This error should be raised when a dictionary redirects the user to another word.

    For example, Cambridge Dictionary redirects the user to the present form of the past tense verb (clicked -> click).
    Under that circumstance, the dictionary should raise this error and pass "click" to the constructor.
    """

    def __init__(self, redirected_word: str):
        if redirected_word is None:
            raise TypeError("redirected_word cannot be None")
        super().__init__(f"Definition is redirected to '{redirected_word}.")
        self.redirected_word = redirected_word


@dataclass
class DictionaryInfo:
    name: str
    icon: str | None = None


class Provider(ABC):
    _ID: str = ""
    _NAME: str = ""
    _DICTIONARIES: dict[str, DictionaryInfo] = {}
    _ICON: str | None = None

    config: dict | None

    @staticmethod
    def browser_headers() -> dict[str, str]:
        return _header_generator.generate()

    @classmethod
    def id(cls) -> str:
        return cls._ID

    @classmethod
    def name(cls) -> str:
        return cls._NAME

    @classmethod
    def supported_dictionaries(cls) -> dict[str, DictionaryInfo]:
        return cls._DICTIONARIES

    @classmethod
    def icon(cls) -> str | None:
        return cls._ICON

    @abstractmethod
    def fetch_definition(self, dictionary_id: str, word: str, *, download_audio: bool = False) -> Definition:
        raise NotImplementedError

    def get_dictionary_info(self, dictionary_id: str) -> DictionaryInfo | None:
        return self.supported_dictionaries().get(dictionary_id)
