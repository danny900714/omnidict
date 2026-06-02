from abc import ABC, abstractmethod

from ..dictionary import Definition


class Dictionary(ABC):
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_definition(self, word: str) -> Definition:
        raise NotImplementedError


class Provider(ABC):
    config: dict

    @classmethod
    @abstractmethod
    def id(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dictionaries(self) -> list[Dictionary]:
        raise NotImplementedError
