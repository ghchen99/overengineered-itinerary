"""
Internal data models for travel processing
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class TravelRequest:
    """Internal data class to structure travel request parameters."""
    destination_city: str
    destination_country: str
    depart_date: str
    return_date: str
    priority: str = "all"
    budget_level: str = "flexible"
    departure_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    additional_preferences: Optional[str] = None

    def __post_init__(self):
        """Basic validation and normalization."""
        self.priority = self.priority.lower().strip()
        self.budget_level = self.budget_level.lower().strip()