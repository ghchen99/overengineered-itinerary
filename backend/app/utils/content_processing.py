"""
Content processing utilities for markdown and text manipulation
"""

def extract_markdown_content(raw_content: str) -> str:
    """Extract clean markdown content from agent response."""
    content = raw_content.strip()
    
    # Remove agent completion markers
    markers_to_remove = [
        "ITINERARY_COMPLETE - Ready for ImagesAgent",
        "IMAGES_COMPLETE - Ready for FlightsAgent", 
        "FLIGHTS_COMPLETE - Ready for AccommodationAgent",
        "ACCOMMODATION_COMPLETE - Ready for CriticAgent",
        "DOCUMENT_READY"
    ]
    
    for marker in markers_to_remove:
        content = content.replace(marker, "").strip()
    
    # Remove markdown code block markers if present
    if content.startswith('```markdown'):
        content = content[11:].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
    elif content.startswith('```'):
        content = content[3:].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
    
    return content