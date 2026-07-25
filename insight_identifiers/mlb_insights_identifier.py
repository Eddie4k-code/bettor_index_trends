from interfaces.insights_identifier import InsightsIdentifier
from schemas.insights_identifier_input import InsightsIdentifierInput

class MLBInsightsIdentifier(InsightsIdentifier):
    def identify_insights(self, prop_bet: PropBet) -> list[str]:
        # Shared

    def _check_ten_game_hit_rate_is_hot(self, PropBet: PropBet) -> bool:
        pass


    def _check_line_below_players_season_average(self, PropBet: PropBet) -> bool:
        pass


    def _check_venue_hot_tonight(self, PropBet: PropBet) -> bool:
        pass