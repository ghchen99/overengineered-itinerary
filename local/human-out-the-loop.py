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
    """Create a sequential team that builds a single cohesive markdown document."""
    
    # Itinerary Agent - Creates the initial structure and detailed itinerary
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Creates the initial travel document structure and detailed day-by-day itinerary.",
        system_message="""You are the lead itinerary planner. You START the travel planning document.

Your job is to create a comprehensive travel plan document in proper markdown format. Include placeholder sections that other agents will replace.

IMPORTANT FORMATTING RULES:
1. Start with a clear markdown document structure
2. Use proper markdown headers (# ## ###)
3. Include placeholder text that other agents can easily find and replace
4. Make sure your output is a complete, well-formatted markdown document

Use this EXACT structure:
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

<!-- FLIGHTS_PLACEHOLDER -->

<!-- ACCOMMODATION_PLACEHOLDER -->

## 💡 Travel Tips & Practical Information
[Include local tips, booking advice, cultural notes]
```

After creating the document, end with: "ITINERARY_COMPLETE - Ready for FlightsAgent".""",
        model_client=model_client,
    )
    
    # Flights Agent - Replaces flight placeholder with actual flight information
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Adds flight booking information to the existing travel document.",
        system_message="""You are the flight specialist. You will receive a complete travel document with a flights placeholder.

Your job is to:
1. Take the ENTIRE existing travel document 
2. Use the view_flights tool to get flight booking links
3. Replace "<!-- FLIGHTS_PLACEHOLDER -->" with the actual flight section
4. Return the COMPLETE updated document with all original content intact

CRITICAL: You must return the entire document with ONLY the flights placeholder replaced. Keep everything else exactly the same.

Look for the placeholder "<!-- FLIGHTS_PLACEHOLDER -->" and replace it with the flight information from the tool.

After updating, end with: "FLIGHTS_COMPLETE - Ready for AccommodationAgent".""",
        model_client=model_client,
        tools=[view_flights],
    )
    
    # Accommodation Agent - Replaces accommodation placeholder with actual accommodation information
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Adds accommodation information to the existing travel document.",
        system_message="""You are the accommodation specialist. You will receive a complete travel document with an accommodation placeholder.

Your job is to:
1. Take the ENTIRE existing travel document
2. Use the find_airbnb_accommodation tool to get accommodation links for each recommended base location
3. Replace "<!-- ACCOMMODATION_PLACEHOLDER -->" with a complete accommodation section
4. Return the COMPLETE final travel document with all content intact

CRITICAL: You must return the entire document with ONLY the accommodation placeholder replaced. Keep everything else exactly the same.

Create a proper accommodation section like:
```markdown
## 🏠 Accommodation Options

**Dates:** [checkin] to [checkout]  
**Guests:** [number]

[Use find_airbnb_accommodation for each recommended location and format the results properly]
```

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
4. Output "DOCUMENT_READY" followed by the final, clean markdown document

If the document is complete and properly formatted, respond with:
DOCUMENT_READY

[Insert the complete final markdown document here]

If anything is missing or incorrect, provide specific feedback on what needs to be fixed.""",
        model_client=model_client,
    )
    
    # Combined termination conditions
    max_msg_termination = MaxMessageTermination(max_messages=20)
    text_termination = TextMentionTermination("DOCUMENT_READY")
    combined_termination = max_msg_termination | text_termination
    
    # Create sequential team using RoundRobinGroupChat
    team = RoundRobinGroupChat(
        participants=[itinerary_agent, flights_agent, accommodation_agent, critic_agent],
        termination_condition=combined_termination,
    )
    
    return team


def save_markdown_document(content: str, filename: str = None):
    """Save the final markdown document to a file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"travel_plan_{timestamp}.md"
    
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


async def run_sequential_travel_planner(travel_request: str):
    """Run the sequential travel planner and save the final markdown document."""
    print(f"\n{'='*80}\nRunning Sequential Travel Planner\n{'='*80}\n")
    
    model_client = create_model_client()
    final_document = ""
    
    try:
        # Create the sequential team
        team = create_sequential_travel_team(model_client)
        
        # Run the team with the travel request
        stream = team.run_stream(task=travel_request)
        
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
    
    # Save the final document if we captured it
    if final_document:
        saved_file = save_markdown_document(final_document)
        if saved_file:
            print(f"\n🎉 Complete travel plan generated and saved!")
            print(f"📄 File: {saved_file}")
    else:
        print("\n⚠️  Warning: Final document was not captured properly")


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
    
    await run_sequential_travel_planner(travel_request)


if __name__ == "__main__":
    asyncio.run(main())