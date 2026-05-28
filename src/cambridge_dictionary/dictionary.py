from enum import StrEnum

class Example:
    sentence: str
    translation: str

class Sense:
    definition: str
    translation: str
    examples: list[Example]

class PartOfSpeech(StrEnum):
    NOUN = "noun"
    PRONOUN = "pronoun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    DETERMINER = "determiner"

class Entry:
    phonemic_transcription_us: str
    phonemic_transcription_uk: str
    part_of_speech: PartOfSpeech
    senses: list[Sense]

class Definition:
    word: str
    entries: list[Entry]

    def get_html(self):
        pass
