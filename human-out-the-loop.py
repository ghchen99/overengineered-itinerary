import os
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from datetime import datetime, timedelta

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

        response_message = f"""
## ✈️ Flight Options

**Route:** {from_location} → {to_location}  
**Dates:** {depart_date} to {return_date}

### Booking Links:
- 🔗 **[Kayak - Compare Prices]({kayak_url})**
- 🔗 **[Skyscanner - Flexible Dates]({skyscanner_url})**
"""
        
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
## 🏠 Accommodation Options

**Location:** {destination}  
**Dates:** {checkin} to {checkout}  
**Guests:** {guests}

### Booking Link:
- 🔗 **[Browse Airbnb Properties]({airbnb_url})**

*Includes entire homes, private rooms, and unique local experiences*
"""
        
        return response_message
        
    except Exception as e:
        error_msg = f"Error generating Airbnb URL for {destination}: {str(e)}"
        print(error_msg)
        return error_msg


def create_model_client():
    """Create and return the Azure OpenAI model client."""
    return AzureOpenAIChatCompletionClient(
        model=os.environ["AZURE_OPENAI_MODEL_NAME"],
        azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


def create_sequential_travel_team(model_client):
    """Create a sequential team of travel specialists that build a shared document."""
    
    # Itinerary Agent - Creates the initial structure and detailed itinerary
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Creates the initial travel document structure and detailed day-by-day itinerary.",
        system_message="""You are the lead itinerary planner. You START the travel planning document.

Your job is to:
1. Create the initial structure of a comprehensive travel plan document
2. Add detailed day-by-day itinerary with specific attractions, activities, and timing
3. Recommend the best cities/neighborhoods to stay in
4. Include placeholder sections for flights and accommodation that other agents will fill

IMPORTANT: You must start your response with the complete travel document in markdown format. Other agents will modify and enhance this document.

Use this structure:
```markdown
# 🌟 [DESTINATION] Travel Plan

## 📋 Trip Overview
- **Duration:** [X] days
- **Dates:** [dates]
- **Travelers:** [number]
- **Budget:** [budget level]

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

## ✈️ Flight Information
*[To be filled by FlightsAgent]*

## 🏠 Accommodation Options  
*[To be filled by AccommodationAgent]*

## 💡 Travel Tips & Practical Information
[Include local tips, booking advice, cultural notes]
```

Make your itinerary detailed, realistic, and tailored to the destination and traveler preferences.

After creating the document, end your message with: "ITINERARY_COMPLETE - Ready for FlightsAgent".""",
        model_client=model_client,
    )
    
    # Flights Agent - Adds flight information to the document
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Adds flight booking information to the existing travel document.",
        system_message="""You are the flight specialist. You will receive a travel document that already has an itinerary.

Your job is to:
1. Take the existing travel document 
2. Use the view_flights tool to get flight booking links
3. Replace the "Flight Information" section with actual flight options and links
4. Return the COMPLETE updated document

When you see the travel document, look for:
- Origin and destination locations
- Travel dates from the itinerary
- Replace "*[To be filled by FlightsAgent]*" with actual flight information

Always use the view_flights tool and then provide the complete updated travel document with the flight section filled in.

After updating the document, end your message with: "FLIGHTS_COMPLETE - Ready for AccommodationAgent".""",
        model_client=model_client,
        tools=[view_flights],
    )
    
    # Accommodation Agent - Adds accommodation information to the document
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Adds accommodation information to the existing travel document.",
        system_message="""You are the accommodation specialist. You will receive a travel document that already has an itinerary and flight information.

Your job is to:
1. Take the existing travel document
2. Use the find_airbnb_accommodation tool to get accommodation links for each recommended base location
3. Replace the "Accommodation Options" section with actual Airbnb links and recommendations
4. Add accommodation links directly to relevant days in the itinerary where location changes occur
5. Return the COMPLETE final travel document

When you see the travel document, look for:
- Recommended base locations from the itinerary
- Travel dates 
- Number of travelers
- Replace "*[To be filled by AccommodationAgent]*" with actual accommodation options

Use find_airbnb_accommodation for each major city/area mentioned in the "Recommended Base Locations" section. Add the accommodation links both in the main section and inline with relevant itinerary days.

After completing all accommodations, end your message with: "TRAVEL_PLAN_COMPLETE - All sections finalized!".""",
        model_client=model_client,
        tools=[find_airbnb_accommodation],
    )
    
    # Multiple termination conditions to ensure completion
    # Option 1: Use a higher message limit to account for tool calls
    max_messages_termination = MaxMessageTermination(max_messages=10)
    
    # Option 2: Terminate when final completion message is seen
    completion_termination = TextMentionTermination("TRAVEL_PLAN_COMPLETE")
    
    # Create sequential team using RoundRobinGroupChat
    team = RoundRobinGroupChat(
        participants=[itinerary_agent, flights_agent, accommodation_agent],
        termination_condition=completion_termination,  # Use text-based termination
    )
    
    return team


def create_sequential_travel_team_alternative(model_client):
    """Alternative approach: Create team with higher message limit and clearer agent coordination."""
    
    # Itinerary Agent
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Creates the initial travel document structure and detailed day-by-day itinerary.",
        system_message="""You are the lead itinerary planner. You START the travel planning document.

Create a comprehensive travel plan with detailed day-by-day itinerary. Include placeholder sections for flights and accommodation.

After creating the document, simply say: "Itinerary complete. FlightsAgent, please add flight information."

Format your document with clear sections and make it easy for other agents to update.""",
        model_client=model_client,
    )
    
    # Flights Agent
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Adds flight booking information to the existing travel document.",
        system_message="""You are the flight specialist. Update the travel document with flight information.

1. Use the view_flights tool to get flight booking links
2. Replace the flight placeholder section with actual flight options
3. Return the COMPLETE updated document
4. End with: "Flights added. AccommodationAgent, please add accommodation options." """,
        model_client=model_client,
        tools=[view_flights],
    )
    
    # Accommodation Agent
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Adds accommodation information to finalize the travel document.",
        system_message="""You are the accommodation specialist. Complete the travel document with accommodation information.

1. Use find_airbnb_accommodation for each recommended location
2. Replace accommodation placeholders with actual options
3. Return the COMPLETE final travel document
4. End with: "Travel plan complete! All sections finalized." """,
        model_client=model_client,
        tools=[find_airbnb_accommodation],
    )
    
    # Use higher message limit to ensure all agents get their turn
    termination = MaxMessageTermination(max_messages=15)
    
    team = RoundRobinGroupChat(
        participants=[itinerary_agent, flights_agent, accommodation_agent],
        termination_condition=termination,
    )
    
    return team


async def run_sequential_travel_planner(travel_request: str, use_alternative: bool = False):
    """Run the sequential travel planner where each agent enhances a shared document."""
    print(f"\n{'='*80}\nRunning Sequential Travel Planner\n{'='*80}\n")
    
    model_client = create_model_client()
    
    try:
        # Create the sequential team
        if use_alternative:
            team = create_sequential_travel_team_alternative(model_client)
        else:
            team = create_sequential_travel_team(model_client)
        
        # Run the team with the travel request
        stream = team.run_stream(task=travel_request)
        
        # Display the conversation
        await Console(stream)
    finally:
        # Close model client connections
        await model_client.close()


async def main():
    """Main function to run the travel planner."""
    
    # Example travel request
    travel_request = """
    I want to plan a trip to Tokyo, Japan for 7 days in October 2025. 
    I'll be traveling from London (LHR). I'm interested in seeing temples, 
    trying authentic Japanese food, and experiencing the city culture.
    I need help with flights, accommodation, and a detailed itinerary.
    My budget is flexible but I prefer good value options.
    """
    
    # Try the improved version first
    print("=== Running with Text Termination (Recommended) ===")
    await run_sequential_travel_planner(travel_request, use_alternative=False)
    
    # Uncomment to try the alternative approach
    # print("\n=== Running with Higher Message Limit (Alternative) ===")
    # await run_sequential_travel_planner(travel_request, use_alternative=True)


if __name__ == "__main__":
    asyncio.run(main())