from abc import abstractmethod, ABC
from collections.abc import Iterator


class SiteParser(ABC):
    @abstractmethod
    def list_urls(self, html: str, base_url: str) -> Iterator[str]:
        pass

    @abstractmethod
    def extract_text(self, html: str) -> str:
        pass