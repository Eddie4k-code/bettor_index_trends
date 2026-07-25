class InsightsIdentifier(ABC):
    @abstractmethod
    def identify_insights(self, prop_bet: PropBet) -> list[str]:
        """
        Flags for notable insights for a particular prop.
        """
        pass