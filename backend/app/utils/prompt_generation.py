"""
Prompt generation utilities for AI agents
"""
from datetime import datetime
from ..models.travel import TravelRequest

def generate_travel_prompt(request: TravelRequest) -> str:
    """Generate a natural travel request prompt from structured input."""
    
    # Calculate trip duration
    depart_dt = datetime.strptime(request.depart_date, "%Y-%m-%d")
    return_dt = datetime.strptime(request.return_date, "%Y-%m-%d")
    duration = (return_dt - depart_dt).days
    
    # Format dates nicely for the prompt
    depart_formatted = depart_dt.strftime("%B %d, %Y")
    return_formatted = return_dt.strftime("%B %d, %Y")
    
    # Map priority to interests
    priority_mapping = {
        "scenery": "seeing beautiful landscapes, scenic views, and natural attractions",
        "food": "trying authentic local cuisine, visiting markets, and food experiences",
        "history": "exploring historical sites, museums, and cultural landmarks",
        "culture": "experiencing local culture, traditions, and authentic activities",
        "all": "experiencing everything the destination has to offer - culture, food, history, and scenery"
    }
    
    interests = priority_mapping.get(request.priority, priority_mapping["all"])
    
    # Build the prompt
    departure_info = f"from {request.departure_airport}" if request.departure_airport else "from my location"
    destination_info = f"to {request.destination_airport}" if request.destination_airport else ""
    
    prompt = f"""I want to plan a trip to {request.destination_city}, {request.destination_country} for {duration} days from {depart_formatted} to {return_formatted}.

I'll be traveling {departure_info} {destination_info}. 

I'm interested in {interests}.

I need help with flights, accommodation, and a detailed itinerary. My budget is {request.budget_level} but I prefer good value options."""

    if request.additional_preferences:
        prompt += f"\n\nAdditional preferences: {request.additional_preferences}"
    
    return prompt