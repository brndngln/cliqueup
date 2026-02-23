"""
Elo Rating System for squad matching algorithm.
Inspired by chess rankings, adapted for squad-based dating.
"""
from ..core.config import settings


class EloRating:
    """
    Elo rating calculator for squad matching.
    
    Higher Elo = more desirable/successful in matching.
    Updates based on swipe outcomes.
    """
    
    @staticmethod
    def expected_score(rating_a: int, rating_b: int) -> float:
        """Calculate expected score for rating_a vs rating_b."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    @staticmethod
    def update_rating(
        current_rating: int,
        opponent_rating: int,
        outcome: float,  # 1.0 = liked us, 0.0 = passed on us
        k_factor: int = None
    ) -> int:
        """
        Update Elo rating based on match outcome.
        
        Args:
            current_rating: Current Elo rating
            opponent_rating: Opponent's Elo rating
            outcome: 1.0 if they liked us, 0.0 if they passed
            k_factor: Rating adjustment factor (default from settings)
        
        Returns:
            New Elo rating
        """
        if k_factor is None:
            k_factor = settings.ELO_K_FACTOR
        
        expected = EloRating.expected_score(current_rating, opponent_rating)
        new_rating = current_rating + k_factor * (outcome - expected)
        return max(100, int(new_rating))  # Minimum 100 rating
    
    @staticmethod
    def calculate_squad_rating(member_ratings: list[int]) -> int:
        """
        Calculate aggregate squad rating from member ratings.
        Uses weighted average favoring higher-rated members.
        """
        if not member_ratings:
            return settings.DEFAULT_ELO
        
        # Sort descending and weight higher ratings more
        sorted_ratings = sorted(member_ratings, reverse=True)
        weighted_sum = 0
        weight_total = 0
        
        for i, rating in enumerate(sorted_ratings):
            weight = len(sorted_ratings) - i  # Higher weight for top members
            weighted_sum += rating * weight
            weight_total += weight
        
        return int(weighted_sum / weight_total) if weight_total > 0 else settings.DEFAULT_ELO
    
    @staticmethod
    def match_score(squad_a_rating: int, squad_b_rating: int) -> float:
        """
        Calculate match compatibility score between two squads.
        Returns 0-1 score, higher = more compatible.
        """
        rating_diff = abs(squad_a_rating - squad_b_rating)
        # Closer ratings = better match (up to 200 point difference is ideal)
        if rating_diff <= 200:
            return 1.0 - (rating_diff / 400)
        return max(0.2, 1.0 - (rating_diff / 800))
