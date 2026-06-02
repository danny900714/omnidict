from .chinese_dictionary import ChineseDictionary
from ..common import Provider, Dictionary


class CambridgeDictionaryProvider(Provider):
    @classmethod
    def id(cls) -> str:
        return "cambridge-dictionary"

    @classmethod
    def name(cls) -> str:
        return "Cambridge Dictionary"

    @property
    def dictionaries(self) -> list[Dictionary]:
        return [
            ChineseDictionary("english-chinese-simplified", "English-Chinese (Simplified)"),
            ChineseDictionary("english-chinese-traditional", "English-Chinese (Traditional)"),
        ]
