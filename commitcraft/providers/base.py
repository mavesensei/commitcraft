from abc import ABC, abstractmethod


class Provider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def generate_commit_message(self, context: str) -> str: ...

    @abstractmethod
    def generate_pr_description(self, context: str) -> str: ...

    @abstractmethod
    def generate_release_notes(self, context: str) -> str: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def describe_change(self, context: str) -> str: ...
