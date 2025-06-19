from abc import ABC, abstractmethod
from collections import Counter


class BaseParser(ABC):
    @abstractmethod
    def parse(self, data) -> Counter:
        pass