from typing import Optional

from bs4 import BeautifulSoup


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

    def __init__(self, senses: list[Sense], *, part_of_speech: Optional[str] = None,
                 phonemic_transcriptions: Optional[dict[str, str]]):
        self.part_of_speech = part_of_speech
        self.phonemic_transcriptions = phonemic_transcriptions
        self.senses = senses


class Definition:
    word: str
    entries: list[Entry]

    def __init__(self, word: str, entries: list[Entry]):
        self.word = word
        self.entries = entries

    def render_html(self, *, include_phonemic_transcriptions: bool = True, include_translation: bool = True,
                    include_examples: bool = False) -> str:
        soup = BeautifulSoup("", "html.parser")
        soup.append(soup.new_tag("style", string="ol > li:not(:last-child) { margin-bottom: 0.25rem; }"))
        root = soup.new_tag("div", style="text-align: start")
        soup.append(root)

        for entry in self.entries:
            root.append(soup.new_tag("b", string=self.word))

            # Render phonemic transcriptions
            if include_phonemic_transcriptions and entry.phonemic_transcriptions is not None:
                for i, (region, transcription) in enumerate(entry.phonemic_transcriptions.items()):
                    margin_left = "1rem" if i == 0 else "0.75rem"
                    root.append(
                        soup.new_tag("span", style=f"color: var(--fg-disabled); margin-left: {margin_left}",
                                     string=region))
                    root.append(
                        soup.new_tag("span", style=f"color: var(--fg-subtle); margin-left: 0.375rem",
                                     string=transcription))

            # Render part of speech
            if entry.part_of_speech is not None:
                root.append(
                    soup.new_tag("i", style="color: var(--fg-subtle); margin-left: 1rem", string=entry.part_of_speech))

            root.append(soup.new_tag("br"))

            # Render senses list
            ol = soup.new_tag("ol", style="gap: 0.5rem")
            root.append(ol)
            for sense in entry.senses:
                li = soup.new_tag("li", string=sense.definition)
                ol.append(li)

                # Insert features before the definition
                if sense.features is not None:
                    features_span = soup.new_tag("span", style="color: var(--fg-subtle); margin-right: 0.75rem",
                                                 string=sense.features)
                    li.insert(0, features_span)

                # Append translation after the definition
                if include_translation and sense.translation is not None:
                    li.append(soup.new_tag("br"))
                    li.append(soup.new_tag("span", style="color: var(--flag-4)", string=sense.translation))

                # Append the example list
                if include_examples and sense.examples is not None:
                    li.append(soup.new_tag("br"))
                    ul = soup.new_tag("ul")
                    li.append(ul)
                    for example in sense.examples:
                        li_example = soup.new_tag("li", string=example.sentence)
                        ul.append(li_example)
                        if include_translation and example.translation is not None:
                            li_example.append(soup.new_tag("br"))
                            li_example.append(
                                soup.new_tag("span", style="color: var(--flag-4)", string=example.translation))

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

    redirected_word: str

    def __init__(self, redirected_word: str):
        if redirected_word is None:
            raise TypeError("redirected_word cannot be None")
        super().__init__(f"Definition is redirected to '{redirected_word}.")
        self.redirected_word = redirected_word
