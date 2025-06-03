import os
import asyncio
import json
from dataclasses import dataclass, asdict
from typing import Optional, AsyncGenerator
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# FastAPI app
app = FastAPI(title="Travel Planner API", version="1.0.0")

# Pydantic models for API
class TravelPlanRequest(BaseModel):
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
    type: str  # "progress", "markdown_update", "final", "error"
    agent: Optional[str] = None
    content: str
    timestamp: str
    character_count: Optional[int] = None

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

def create_model_client():
    """Create and return the Azure OpenAI model client."""
    return AzureOpenAIChatCompletionClient(
        model=os.environ["AZURE_OPENAI_MODEL_NAME"],
        azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

def create_sequential_travel_team(model_client, travel_request: TravelRequest):
    """Create a sequential team that builds a single cohesive markdown document."""
    
    # Enhanced Itinerary Agent
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Creates personalized travel document based on user preferences.",
        system_message=f"""You are the lead itinerary planner. You START the travel planning document.

TRIP DETAILS:
- Destination: {travel_request.destination_city}, {travel_request.destination_country}
- Priority Focus: {travel_request.priority}
- Budget Level: {travel_request.budget_level}

Your job is to create a comprehensive travel plan document in proper markdown format tailored to these preferences.

IMPORTANT FORMATTING RULES:
1. Start with a clear markdown document structure
2. Use proper markdown headers (# ## ###)
3. Include placeholder text that other agents can easily find and replace
4. Make sure your output is a complete, well-formatted markdown document
5. Tailor activities to the user's priority focus ({travel_request.priority})

Use this EXACT structure:
```markdown
# 🌟 {travel_request.destination_city}, {travel_request.destination_country} Travel Plan

## 📋 Trip Overview
- **Duration:** [X] days
- **Dates:** {travel_request.depart_date} to {travel_request.return_date}
- **Budget:** {travel_request.budget_level}
- **Focus:** {travel_request.priority}

## 🗺️ Recommended Base Locations
[List strategic cities/areas to stay with brief explanations]

## 📅 Day-by-Day Itinerary

### Day 1: [Theme/Focus]
**Morning (9:00-12:00)**
- [Activity with specific location and details]

**Afternoon (12:00-17:00)** 
- [Activity with specific location and details]

**Evening (17:00-21:00)**
- [Activity with specific location and details]

[Continue for each day...]

<!-- FLIGHTS_PLACEHOLDER -->

<!-- ACCOMMODATION_PLACEHOLDER -->

## 💡 Travel Tips & Practical Information
[Include local tips, booking advice, cultural notes]
```

After creating the document, end with: "ITINERARY_COMPLETE - Ready for ImagesAgent".""",
        model_client=model_client,
    )
    
    # Images Agent
    images_agent = AssistantAgent(
        name="ImagesAgent",
        description="Adds Google image search links to notable locations in the Day-by-Day Itinerary section.",
        system_message="""You are the images specialist. You will receive a complete travel document with a detailed itinerary.

Your job is to:
1. Take the ENTIRE existing travel document
2. Identify notable locations, attractions, temples, landmarks, restaurants, and places mentioned in the "## 📅 Day-by-Day Itinerary" section ONLY
3. Generate Google Images search URLs for these locations using this format:
   - Clean the location name (remove special characters, replace spaces with +)
   - Create URL: https://www.google.com/search?q=[LOCATION_NAME_ENCODED]&tbm=isch
   - Example: "Tokyo Tower" becomes "https://www.google.com/search?q=Tokyo+Tower&tbm=isch"
4. Replace location names with markdown links: [Location Name](Google Images URL)
5. Return the COMPLETE updated document with enhanced itinerary links

GOOGLE IMAGES URL GENERATION RULES:
- Replace spaces with + signs
- Replace commas with %2C
- Keep alphanumeric characters and common punctuation
- Format: https://www.google.com/search?q=[encoded_location]&tbm=isch

CRITICAL RULES:
- ONLY modify the "## 📅 Day-by-Day Itinerary" section
- Keep everything else exactly the same
- Format should be: [Location Name](Google Images URL)
- Only add links to specific places, attractions, landmarks, temples, restaurants, etc.
- Don't add links to generic words like "train", "hotel", "lunch"

After updating, end with: "IMAGES_COMPLETE - Ready for FlightsAgent".""",
        model_client=model_client,
    )
    
    # Flights Agent
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Adds flight booking information using user's travel details.",
        system_message=f"""You are the flight specialist. You will receive a complete travel document with a flights placeholder.

USER'S FLIGHT DETAILS:
- Departure Airport: {travel_request.departure_airport or 'Not specified - please infer appropriate airport'}
- Destination Airport: {travel_request.destination_airport or 'Not specified - please infer appropriate airport for the destination'}
- Depart Date: {travel_request.depart_date}
- Return Date: {travel_request.return_date}

AIRPORT INFERENCE GUIDE:
- For major cities, use the main international airport
- Tokyo: NRT (Narita) or HND (Haneda)
- London: LHR (Heathrow), LGW (Gatwick), or STN (Stansted)
- Paris: CDG (Charles de Gaulle)
- New York: JFK or LGA
- Use common sense for other destinations

FLIGHT URL GENERATION:
Once you determine the appropriate airports, generate these booking URLs:

1. KAYAK URL FORMAT:
   https://www.kayak.co.uk/flights/[FROM]-[TO]/[YYYY-MM-DD]/[YYYY-MM-DD]?sort=bestflight_a

2. SKYSCANNER URL FORMAT:
   https://www.skyscanner.net/transport/flights/[from_lower]/[to_lower]/[YYMMDD]/[YYMMDD]/

CRITICAL: You must preserve ALL existing content including all Google Images links added by ImagesAgent.

Only replace the <!-- FLIGHTS_PLACEHOLDER --> section with:

```markdown
## ✈️ Flight Information

**Route:** [FROM] → [TO]  
**Dates:** [DEPART_DATE] to [RETURN_DATE]

### Booking Links:
- 🔗 **[Kayak - Compare Prices]([KAYAK_URL])**
- 🔗 **[Skyscanner - Flexible Dates]([SKYSCANNER_URL])**
```

After updating, end with: "FLIGHTS_COMPLETE - Ready for AccommodationAgent".""",
        model_client=model_client,
    )
    
    # Accommodation Agent
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Adds accommodation information using user's travel details.",
        system_message=f"""You are the accommodation specialist. You will receive a complete travel document with an accommodation placeholder.

USER'S ACCOMMODATION DETAILS:
- Destination: {travel_request.destination_city}, {travel_request.destination_country}
- Check-in: {travel_request.depart_date}
- Check-out: {travel_request.return_date}

AIRBNB URL GENERATION:
For each recommended base location, generate Airbnb search URLs using this format:
https://www.airbnb.co.uk/s/[FORMATTED_DESTINATION]/homes?checkin=[YYYY-MM-DD]&checkout=[YYYY-MM-DD]&adults=2

DESTINATION FORMATTING RULES:
- Replace commas with "--"
- Replace spaces with "-"

Your job is to:
1. Take the ENTIRE existing travel document
2. Identify each recommended base location from the "🗺️ Recommended Base Locations" section
3. Generate Airbnb URLs for each location
4. Replace "<!-- ACCOMMODATION_PLACEHOLDER -->" with:

```markdown
## 🏠 Accommodation Options

### Recommended Areas:

#### [Location 1 Name]
- 🔗 **[Browse Airbnb Properties]([AIRBNB_URL_1])**

[Continue for each base location...]

### Booking Tips:
- Book early for better rates and availability
- Consider proximity to public transportation
- Read recent reviews for the most accurate information
- Look for properties with flexible cancellation policies
```

After completing, end with: "ACCOMMODATION_COMPLETE - Ready for CriticAgent".""",
        model_client=model_client,
    )
    
    # Critic Agent
    critic_agent = AssistantAgent(
        name="CriticAgent",
        description="Reviews the complete travel document and outputs the final markdown.",
        system_message="""You are the quality control critic and final document processor.

Your job is to:
1. Review the complete travel document for quality and completeness
2. Ensure no placeholders remain
3. Check that the document follows proper markdown formatting
4. Output "DOCUMENT_READY" followed by the final, clean markdown document

If the document is complete, respond with:
DOCUMENT_READY

[Insert the complete final markdown document here]""",
        model_client=model_client,
    )
    
    # Combined termination conditions
    max_msg_termination = MaxMessageTermination(max_messages=25)
    text_termination = TextMentionTermination("DOCUMENT_READY")
    combined_termination = max_msg_termination | text_termination
    
    # Create sequential team
    team = RoundRobinGroupChat(
        participants=[itinerary_agent, images_agent, flights_agent, accommodation_agent, critic_agent],
        termination_condition=combined_termination,
    )
    
    return team

async def stream_travel_plan(travel_request: TravelRequest) -> AsyncGenerator[str, None]:
    """Stream travel plan generation with real-time updates."""
    
    model_client = None
    
    try:
        # Initial setup message
        yield json.dumps(StreamMessage(
            type="progress",
            content=f"🚀 Starting travel plan generation for {travel_request.destination_city}, {travel_request.destination_country}",
            timestamp=datetime.now().isoformat()
        ).dict()) + "\n"
        
        # Generate travel prompt
        travel_prompt = generate_travel_prompt(travel_request)
        
        yield json.dumps(StreamMessage(
            type="progress",
            content="📝 Generated travel prompt and initializing AI agents...",
            timestamp=datetime.now().isoformat()
        ).dict()) + "\n"
        
        # Create model client and team
        model_client = create_model_client()
        team = create_sequential_travel_team(model_client, travel_request)
        
        yield json.dumps(StreamMessage(
            type="progress",
            content="🤖 AI agents ready - starting collaboration...",
            timestamp=datetime.now().isoformat()
        ).dict()) + "\n"
        
        # Track the latest markdown content
        latest_markdown = ""
        
        # Run the team and stream updates
        stream = team.run_stream(task=travel_prompt)
        
        async for message in stream:
            if hasattr(message, 'content') and hasattr(message, 'source') and message.source:
                agent_name = message.source
                
                # Send progress update
                yield json.dumps(StreamMessage(
                    type="progress",
                    agent=agent_name,
                    content=f"🔄 {agent_name} is working...",
                    timestamp=datetime.now().isoformat()
                ).dict()) + "\n"
                
                # Extract and check for markdown content
                clean_content = extract_markdown_content(message.content)
                
                # Only send markdown updates if content is substantial and markdown-formatted
                if len(clean_content) > 100 and clean_content.startswith('#'):
                    latest_markdown = clean_content
                    
                    # Determine if this is the final document
                    is_final = agent_name == "CriticAgent" and "DOCUMENT_READY" in message.content
                    
                    yield json.dumps(StreamMessage(
                        type="final" if is_final else "markdown_update",
                        agent=agent_name,
                        content=clean_content,
                        timestamp=datetime.now().isoformat(),
                        character_count=len(clean_content)
                    ).dict()) + "\n"
                    
                    if is_final:
                        yield json.dumps(StreamMessage(
                            type="progress",
                            content="✅ Travel plan complete!",
                            timestamp=datetime.now().isoformat()
                        ).dict()) + "\n"
                        break
        
        # If we didn't get a final document, send the latest as final
        if latest_markdown and not latest_markdown.startswith("✅"):
            yield json.dumps(StreamMessage(
                type="final",
                content=latest_markdown,
                timestamp=datetime.now().isoformat(),
                character_count=len(latest_markdown)
            ).dict()) + "\n"
            
    except Exception as e:
        yield json.dumps(StreamMessage(
            type="error",
            content=f"❌ Error generating travel plan: {str(e)}",
            timestamp=datetime.now().isoformat()
        ).dict()) + "\n"
        
    finally:
        if model_client:
            try:
                await model_client.close()
            except:
                pass

@app.post("/generate-travel-plan")
async def generate_travel_plan(request: TravelPlanRequest):
    """Generate a travel plan with streaming updates."""
    
    try:
        # Convert Pydantic model to internal dataclass
        travel_request = TravelRequest(
            destination_city=request.destination_city,
            destination_country=request.destination_country,
            depart_date=request.depart_date,
            return_date=request.return_date,
            priority=request.priority,
            budget_level=request.budget_level,
            departure_airport=request.departure_airport,
            destination_airport=request.destination_airport,
            additional_preferences=request.additional_preferences
        )
        
        return StreamingResponse(
            stream_travel_plan(travel_request),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Travel Planner API",
        "version": "1.0.0",
        "endpoints": {
            "generate_plan": "/generate-travel-plan (POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)