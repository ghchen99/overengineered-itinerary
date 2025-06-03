"""
AI agent definitions and configurations
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

from ..models.travel import TravelRequest

def create_itinerary_agent(model_client, travel_request: TravelRequest):
    """Create the itinerary planning agent"""
    return AssistantAgent(
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

def create_images_agent(model_client):
    """Create the images enhancement agent"""
    return AssistantAgent(
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

def create_flights_agent(model_client, travel_request: TravelRequest):
    """Create the flights booking agent"""
    return AssistantAgent(
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

def create_accommodation_agent(model_client, travel_request: TravelRequest):
    """Create the accommodation booking agent"""
    return AssistantAgent(
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

CRITICAL INSTRUCTIONS:
1. You MUST output the COMPLETE travel document 
2. You MUST preserve ALL existing content including:
   - The complete Day-by-Day Itinerary
   - All Google Images links added by ImagesAgent
   - The Flight Information section added by FlightsAgent
   - All other sections and content
3. ONLY replace the "<!-- ACCOMMODATION_PLACEHOLDER -->" with the accommodation section
4. DO NOT truncate, shorten, or omit any existing content


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

def create_critic_agent(model_client):
    """Create the quality control and final review agent"""
    return AssistantAgent(
        name="CriticAgent",
        description="Reviews the complete travel document and outputs the final markdown.",
        system_message="""You are the quality control critic and final document processor.

Your job is to:
1. Review the complete travel document for quality and completeness
2. Ensure no placeholders remain (<!-- PLACEHOLDER --> tags)
3. Check that the document follows proper markdown formatting
4. PRESERVE all Google Images links added by ImagesAgent
5. PRESERVE all booking links added by FlightsAgent and AccommodationAgent
6. Only make formatting improvements, not content removals

If the document is complete, respond with:
DOCUMENT_READY

[Insert the complete final markdown document here with ALL links preserved]""",
        model_client=model_client,
    )

def create_sequential_travel_team(model_client, travel_request: TravelRequest):
    """Create a sequential team that builds a single cohesive markdown document."""
    
    # Create all agents
    itinerary_agent = create_itinerary_agent(model_client, travel_request)
    images_agent = create_images_agent(model_client)
    flights_agent = create_flights_agent(model_client, travel_request)
    accommodation_agent = create_accommodation_agent(model_client, travel_request)
    critic_agent = create_critic_agent(model_client)
    
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