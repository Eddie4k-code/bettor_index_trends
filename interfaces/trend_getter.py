from abc import ABC, abstractmethod

class TrendGetter(ABC):
    @abstractmethod
    def get_trends(self, symbols: list[str]) -> list[float]:
        pass