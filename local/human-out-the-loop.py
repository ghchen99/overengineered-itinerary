import os
import asyncio
import re
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

@dataclass
class TravelRequest:
    """Data class to structure travel request parameters."""
    destination_city: str
    destination_country: str
    depart_date: str  # Already formatted from frontend
    return_date: str  # Already formatted from frontend
    priority: str = "all"  # scenery/food/history/culture/all
    budget_level: str = "flexible"  # budget/moderate/flexible/luxury
    departure_airport: Optional[str] = None  # Optional, agents can infer
    destination_airport: Optional[str] = None  # Optional, agents can infer
    additional_preferences: Optional[str] = None

    def __post_init__(self):
        """Basic validation and normalization."""
        # Normalize priority
        self.priority = self.priority.lower().strip()
        self.budget_level = self.budget_level.lower().strip()

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
    
    # Build the prompt - let agents infer airports if not provided
    departure_info = f"from {request.departure_airport}" if request.departure_airport else "from my location"
    destination_info = f"to {request.destination_airport}" if request.destination_airport else ""
    
    prompt = f"""I want to plan a trip to {request.destination_city}, {request.destination_country} for {duration} days from {depart_formatted} to {return_formatted}.

I'll be traveling {departure_info} {destination_info}. 

I'm interested in {interests}.

I need help with flights, accommodation, and a detailed itinerary. My budget is {request.budget_level} but I prefer good value options."""

    if request.additional_preferences:
        prompt += f"\n\nAdditional preferences: {request.additional_preferences}"
    
    return prompt

def view_flights(from_location: str = "LHR", to_location: str = "HKG", 
                depart_date: str = None, return_date: str = None) -> str:
    """Generate flight search URLs for easy access to booking sites."""
    # Set default dates if not provided
    if not depart_date:
        depart_datetime = datetime.now() + timedelta(days=1)
        depart_date = depart_datetime.strftime("%Y-%m-%d")
    
    if not return_date:
        return_datetime = datetime.strptime(depart_date, "%Y-%m-%d") + timedelta(days=4)
        return_date = return_datetime.strftime("%Y-%m-%d")
    
    try:
        print(f"Generating flight search URLs from {from_location} to {to_location}")
        print(f"Departure: {depart_date}, Return: {return_date}")
        
        # Convert dates to YYMMDD format for Skyscanner
        depart_date_formatted = datetime.strptime(depart_date, "%Y-%m-%d").strftime("%y%m%d")
        return_date_formatted = datetime.strptime(return_date, "%Y-%m-%d").strftime("%y%m%d")
        
        # Generate URLs for flight booking sites
        kayak_url = f"https://www.kayak.co.uk/flights/{from_location}-{to_location}/{depart_date}/{return_date}?sort=bestflight_a"
        skyscanner_url = f"https://www.skyscanner.net/transport/flights/{from_location.lower()}/{to_location.lower()}/{depart_date_formatted}/{return_date_formatted}/"

        response_message = f"""## ✈️ Flight Information

**Route:** {from_location} → {to_location}  
**Dates:** {depart_date} to {return_date}

### Booking Links:
- 🔗 **[Kayak - Compare Prices]({kayak_url})**
- 🔗 **[Skyscanner - Flexible Dates]({skyscanner_url})**"""
        
        return response_message
        
    except Exception as e:
        error_msg = f"Error generating flight URLs from {from_location} to {to_location}: {str(e)}"
        print(error_msg)
        return error_msg

def find_airbnb_accommodation(destination: str, checkin: str = None, checkout: str = None, guests: int = 2) -> str:
    """Generate Airbnb search URL for accommodation in a destination."""
    # Set default dates if not provided
    if not checkin:
        checkin_datetime = datetime.now() + timedelta(days=1)
        checkin = checkin_datetime.strftime("%Y-%m-%d")
    
    if not checkout:
        checkout_datetime = datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=4)
        checkout = checkout_datetime.strftime("%Y-%m-%d")
    
    try:
        print(f"Generating Airbnb search URL for {destination}")
        print(f"Check-in: {checkin}, Check-out: {checkout}, Guests: {guests}")
        
        # Format destination for Airbnb URLs (replace commas with --)
        formatted_destination = destination.replace(",", "--").replace(" ", "-")
        
        # Generate Airbnb search URL
        airbnb_url = f"https://www.airbnb.co.uk/s/{formatted_destination}/homes?checkin={checkin}&checkout={checkout}&adults={guests}"
        
        response_message = f"""
### {destination}
- 🔗 **[Browse Airbnb Properties]({airbnb_url})**"""
        
        return response_message
        
    except Exception as e:
        error_msg = f"Error generating Airbnb URL for {destination}: {str(e)}"
        print(error_msg)
        return error_msg

def add_image_links(location_name: str) -> str:
    """Generate Google Images search URL for a location."""
    try:
        # Clean the location name for URL encoding
        clean_name = location_name.strip()
        # URL encode the location name
        encoded_name = clean_name.replace(" ", "+").replace(",", "%2C")
        
        # Generate Google Images search URL
        image_url = f"https://www.google.com/search?q={encoded_name}&tbm=isch"
        
        return image_url
        
    except Exception as e:
        print(f"Error generating image URL for {location_name}: {str(e)}")
        return ""

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
    
    # Enhanced Itinerary Agent with user preferences
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
    
    # Images Agent - Adds Google image search links to notable locations in the itinerary
    images_agent = AssistantAgent(
        name="ImagesAgent",
        description="Adds Google image search links to notable locations in the Day-by-Day Itinerary section.",
        system_message="""You are the images specialist. You will receive a complete travel document with a detailed itinerary.

Your job is to:
1. Take the ENTIRE existing travel document
2. Identify notable locations, attractions, temples, landmarks, restaurants, and places mentioned in the "## 📅 Day-by-Day Itinerary" section ONLY
3. Use the add_image_links tool to get Google Images URLs for these locations
4. Replace location names with markdown links that include the Google Images search
5. Return the COMPLETE updated document with enhanced itinerary links

CRITICAL RULES:
- ONLY modify the "## 📅 Day-by-Day Itinerary" section
- Keep everything else exactly the same
- Format should be: [Location Name](Google Images URL)
- Only add links to specific places, attractions, landmarks, temples, restaurants, etc.
- Don't add links to generic words like "train", "hotel", "lunch"

After updating, end with: "IMAGES_COMPLETE - Ready for FlightsAgent".""",
        model_client=model_client,
        tools=[add_image_links],
    )
    
    # Enhanced Flights Agent - lets agents infer airports if not provided
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Adds flight booking information using user's travel details.",
        system_message=f"""You are the flight specialist. You will receive a complete travel document with a flights placeholder.

USER'S FLIGHT DETAILS:
- Departure Airport: {travel_request.departure_airport or 'Not specified - please infer appropriate airport'}
- Destination Airport: {travel_request.destination_airport or 'Not specified - please infer appropriate airport for the destination'}
- Depart Date: {travel_request.depart_date}
- Return Date: {travel_request.return_date}

Your job is to:
1. Take the ENTIRE existing travel document 
2. If airports are not specified, infer appropriate airport codes based on the destination
3. Use the view_flights tool with the appropriate airport details
4. Replace "<!-- FLIGHTS_PLACEHOLDER -->" with the actual flight section
5. Return the COMPLETE updated document with all original content intact

AIRPORT INFERENCE GUIDE:
- For major cities, use the main international airport
- Tokyo: NRT (Narita) or HND (Haneda)
- London: LHR (Heathrow), LGW (Gatwick), or STN (Stansted)
- Paris: CDG (Charles de Gaulle)
- New York: JFK or LGA
- Use common sense for other destinations

After updating, end with: "FLIGHTS_COMPLETE - Ready for AccommodationAgent".""",
        model_client=model_client,
        tools=[view_flights],
    )
    
    # Enhanced Accommodation Agent with user's specific details  
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Adds accommodation information using user's travel details.",
        system_message=f"""You are the accommodation specialist. You will receive a complete travel document with an accommodation placeholder.

USER'S ACCOMMODATION DETAILS:
- Destination: {travel_request.destination_city}, {travel_request.destination_country}
- Check-in: {travel_request.depart_date}
- Check-out: {travel_request.return_date}

Your job is to:
1. Take the ENTIRE existing travel document
2. Use the find_airbnb_accommodation tool for each recommended base location
3. Replace "<!-- ACCOMMODATION_PLACEHOLDER -->" with a complete accommodation section
4. Return the COMPLETE final travel document with all content intact

Use these parameters for the find_airbnb_accommodation tool:
- checkin: {travel_request.depart_date}
- checkout: {travel_request.return_date}
- guests: 2 (default - can be adjusted based on context)

After completing, end with: "ACCOMMODATION_COMPLETE - Ready for CriticAgent".""",
        model_client=model_client,
        tools=[find_airbnb_accommodation],
    )
    
    # Critic Agent - Reviews and outputs final document
    critic_agent = AssistantAgent(
        name="CriticAgent",
        description="Reviews the complete travel document and outputs the final markdown.",
        system_message="""You are the quality control critic and final document processor.

Your job is to:
1. Review the complete travel document for quality and completeness
2. Ensure no placeholders remain (no "<!-- PLACEHOLDER -->" text)
3. Verify all sections are properly filled
4. Verify that notable locations in the itinerary have Google Images links
5. Output "DOCUMENT_READY" followed by the final, clean markdown document

If the document is complete and properly formatted, respond with:
DOCUMENT_READY

[Insert the complete final markdown document here]

If anything is missing or incorrect, provide specific feedback on what needs to be fixed.""",
        model_client=model_client,
    )
    
    # Combined termination conditions
    max_msg_termination = MaxMessageTermination(max_messages=25)
    text_termination = TextMentionTermination("DOCUMENT_READY")
    combined_termination = max_msg_termination | text_termination
    
    # Create sequential team using RoundRobinGroupChat
    team = RoundRobinGroupChat(
        participants=[itinerary_agent, images_agent, flights_agent, accommodation_agent, critic_agent],
        termination_condition=combined_termination,
    )
    
    return team

def save_markdown_document(content: str, travel_request: TravelRequest, filename: str = None):
    """Save the final markdown document to a file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city = re.sub(r'[^\w\-_]', '_', travel_request.destination_city.lower())
        filename = f"travel_plan_{safe_city}_{timestamp}.md"
    
    # Extract the markdown content after "DOCUMENT_READY"
    if "DOCUMENT_READY" in content:
        markdown_content = content.split("DOCUMENT_READY", 1)[1].strip()
    else:
        markdown_content = content
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\n✅ Travel plan saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return None

async def run_sequential_travel_planner(travel_request: TravelRequest, save_locally: bool = True) -> str:
    """Run the sequential travel planner with user input and optionally save the final markdown document.
    
    Args:
        travel_request: The travel request configuration
        save_locally: Whether to save the markdown document to a local file (default: True)
        
    Returns:
        str: The generated markdown travel plan document
    """
    print(f"\n{'='*80}\nRunning Sequential Travel Planner\n{'='*80}\n")
    print(f"Destination: {travel_request.destination_city}, {travel_request.destination_country}")
    print(f"Dates: {travel_request.depart_date} to {travel_request.return_date}")
    print(f"Priority: {travel_request.priority}")
    print(f"Budget: {travel_request.budget_level}")
    if travel_request.departure_airport:
        print(f"Departure Airport: {travel_request.departure_airport}")
    if travel_request.destination_airport:
        print(f"Destination Airport: {travel_request.destination_airport}")
    print()
    
    # Generate the travel prompt from user input
    travel_prompt = generate_travel_prompt(travel_request)
    print("Generated Travel Prompt:")
    print("-" * 40)
    print(travel_prompt)
    print("-" * 40 + "\n")
    
    model_client = create_model_client()
    final_document = ""
    
    try:
        # Create the sequential team with user preferences
        team = create_sequential_travel_team(model_client, travel_request)
        
        # Run the team with the generated prompt
        stream = team.run_stream(task=travel_prompt)
        
        # Capture the final document
        async for message in stream:
            print(f"---------- {type(message).__name__} ({getattr(message, 'source', 'system')}) ----------")
            if hasattr(message, 'content'):
                print(message.content)
                # Capture the final document when critic outputs it
                if hasattr(message, 'source') and message.source == "CriticAgent" and "DOCUMENT_READY" in message.content:
                    final_document = message.content
    finally:
        # Close model client connections
        await model_client.close()
    
    # Save the final document if we captured it and saving is requested
    if final_document:
        if save_locally:
            saved_file = save_markdown_document(final_document, travel_request)
            if saved_file:
                print(f"\n🎉 Complete travel plan generated and saved!")
                print(f"📄 File: {saved_file}")
        else:
            print(f"\n🎉 Complete travel plan generated!")
        
        return final_document
    else:
        print("\n⚠️  Warning: Final document was not captured properly")
        return ""

async def main():
    """Main function to run the travel planner."""

    travel_request = TravelRequest(
        destination_city="Tokyo",
        destination_country="Japan",
        depart_date="2025-10-10",
        return_date="2025-10-17",
        departure_airport="LHR",  # Optional
        priority="food",
        budget_level="flexible",
        additional_preferences="interested in temples and authentic experiences"
    )
    
    # Example usage with local saving (default behavior)
    markdown_plan = await run_sequential_travel_planner(travel_request)
    
    # Example usage without local saving
    # markdown_plan = await run_sequential_travel_planner(travel_request, save_locally=False)
    
    # You can now use the returned markdown document
    if markdown_plan:
        print(f"\nReturned markdown document length: {len(markdown_plan)} characters")

if __name__ == "__main__":
    asyncio.run(main())