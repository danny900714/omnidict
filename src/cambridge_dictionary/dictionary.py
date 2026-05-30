from typing import Optional


class Example:
    sentence: str
    translation: Optional[str]

    def __init__(self, sentence: str, *, translation: Optional[str] = None):
        self.sentence = sentence
        self.translation = translation


class Sense:
    features: Optional[str]
    definition: str
    translation: Optional[str]
    examples: Optional[list[Example]]

    def __init__(self, definition: str, *, features: Optional[str] = None, translation: Optional[str] = None,
                 examples: Optional[list[Example]] = None):
        self.features = features
        self.definition = definition
        self.translation = translation
        self.examples = examples if examples is not None else []


class Entry:
    part_of_speech: Optional[str]
    phonemic_transcriptions: Optional[dict[str, str]]
    senses: list[Sense]

    def __init__(self, senses: list[Sense], *, part_of_speech: Optional[str] = None, phonemic_transcriptions: Optional[dict[str, str]]):
        self.part_of_speech = part_of_speech
        self.phonemic_transcriptions = phonemic_transcriptions
        self.senses = senses


class Definition:
    word: str
    entries: list[Entry]

    def __init__(self, word: str, entries: list[Entry]):
        self.word = word
        self.entries = entries

    def get_html(self):
        pass
