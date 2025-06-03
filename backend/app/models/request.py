"""
Pydantic models for API requests and responses
"""
from typing import Optional
from pydantic import BaseModel

class TravelPlanRequest(BaseModel):
    """API request model for travel plan generation"""
    destination_city: str
    destination_country: str
    depart_date: str  # YYYY-MM-DD format
    return_date: str  # YYYY-MM-DD format
    priority: str = "all"  # scenery/food/history/culture/all
    budget_level: str = "flexible"  # budget/moderate/flexible/luxury
    departure_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    additional_preferences: Optional[str] = None

class StreamMessage(BaseModel):
    """Streaming response message model"""
    type: str  # "progress", "markdown_update", "final", "error"
    agent: Optional[str] = None
    content: str
    timestamp: str
    character_count: Optional[int] = None