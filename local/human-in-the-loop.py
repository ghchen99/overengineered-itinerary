import os
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from datetime import datetime, timedelta


def search_attraction_images(attractions: list, country: str = "") -> str:
    """
    Generate Google Images search URLs for a list of attractions to help users visualize destinations.
    This tool provides direct links to image searches for easy access and inspiration.
    
    Args:
        attractions (list): List of attraction names to search for
        country (str): Country name to add context to searches (optional)
    
    Returns:
        str: Formatted message with clickable URLs for image searches
    """
    try:
        print(f"Generating image search URLs for {len(attractions)} attractions in {country}")
        
        if not attractions:
            return "No attractions provided for image search."
        
        # Build the response message
        country_text = f" in {country}" if country else ""
        response_message = f"""Here are Google Images links to help you visualize these amazing attractions{country_text}:

"""
        
        for i, attraction in enumerate(attractions, 1):
            # Create search query - include country for better context if provided
            search_query = f"{attraction} {country}".strip() if country else attraction
            
            # URL encode the search query
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            
            # Generate Google Images URL
            google_images_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            
            # Add to response message with emoji
            emoji = "🏛️" if any(word in attraction.lower() for word in ["temple", "church", "cathedral", "mosque"]) else \
                   "🏰" if any(word in attraction.lower() for word in ["castle", "palace", "fort"]) else \
                   "🗼" if any(word in attraction.lower() for word in ["tower", "bridge", "statue"]) else \
                   "🏞️" if any(word in attraction.lower() for word in ["park", "garden", "lake", "mountain", "beach"]) else \
                   "🏛️" if any(word in attraction.lower() for word in ["museum", "gallery"]) else \
                   "📍"
            
            response_message += f"{emoji} **{attraction}**:\n{google_images_url}\n\n"
        
        response_message += """Click on any link to view stunning photos and get inspired for your trip! Each search will show you:
- Professional travel photography
- Different angles and perspectives  
- Seasonal variations
- Tourist experiences and activities
- Nearby attractions and views"""
        
        return response_message
        
    except Exception as e:
        error_msg = f"An error occurred while generating image search URLs: {str(e)}"
        print(error_msg)
        return error_msg


def view_flights(from_location: str = "LHR", to_location: str = "HKG", 
                depart_date: str = None, return_date: str = None) -> str:
    """
    Generate flight search URLs for the user to click and explore flight options.
    This tool provides direct links to flight booking sites for easy access.
    
    Args:
        from_location (str): Origin airport code (e.g., "LHR", "JFK", "MAN")
        to_location (str): Destination airport code (e.g., "HKG", "DXB", "BCN")
        depart_date (str): Departure date in YYYY-MM-DD format (defaults to tomorrow)
        return_date (str): Return date in YYYY-MM-DD format (defaults to 5 days after departure)
    
    Returns:
        str: Formatted message with clickable URLs for flight searches
    """
    # Get current year for defaults
    current_year = datetime.now().year
    
    # Set default dates if not provided, ensure current year is used
    if not depart_date:
        depart_datetime = datetime(current_year, datetime.now().month, datetime.now().day) + timedelta(days=1)
        depart_date = depart_datetime.strftime("%Y-%m-%d")
    else:
        # If date provided but year seems old, update to current year
        depart_parsed = datetime.strptime(depart_date, "%Y-%m-%d")
        if depart_parsed.year < current_year:
            depart_parsed = depart_parsed.replace(year=current_year)
            depart_date = depart_parsed.strftime("%Y-%m-%d")
    
    if not return_date:
        return_datetime = datetime.strptime(depart_date, "%Y-%m-%d") + timedelta(days=4)
        return_date = return_datetime.strftime("%Y-%m-%d")
    else:
        # If date provided but year seems old, update to current year
        return_parsed = datetime.strptime(return_date, "%Y-%m-%d")
        depart_parsed = datetime.strptime(depart_date, "%Y-%m-%d")
        if return_parsed.year < current_year:
            return_parsed = return_parsed.replace(year=current_year)
        # If return date is before departure date, assume next year
        if return_parsed < depart_parsed:
            return_parsed = return_parsed.replace(year=return_parsed.year + 1)
        return_date = return_parsed.strftime("%Y-%m-%d")
    
    try:
        print(f"Generating flight search URLs from {from_location} to {to_location}")
        print(f"Departure: {depart_date}, Return: {return_date}")
        
        # Convert dates to YYMMDD format for Skyscanner
        depart_date_formatted = datetime.strptime(depart_date, "%Y-%m-%d").strftime("%y%m%d")
        return_date_formatted = datetime.strptime(return_date, "%Y-%m-%d").strftime("%y%m%d")
        
        # Generate URLs for multiple flight booking sites
        kayak_url = f"https://www.kayak.co.uk/flights/{from_location}-{to_location}/{depart_date}/{return_date}?sort=bestflight_a"
        skyscanner_url = f"https://www.skyscanner.net/transport/flights/{from_location.lower()}/{to_location.lower()}/{depart_date_formatted}/{return_date_formatted}/"

        # Format the response message
        response_message = f"""Here are flight search links for your trip from {from_location} to {to_location} ({depart_date} to {return_date}):

🔗 **Kayak** (Best for comparing prices):
{kayak_url}

🔗 **Skyscanner** (Good for flexible dates):
{skyscanner_url}

Click on any of these links to view current flight options, prices, and availability. I recommend checking multiple sites to compare prices and find the best deals for your travel dates."""
        
        return response_message
        
    except Exception as e:
        error_msg = f"An error occurred while generating flight URLs from {from_location} to {to_location}: {str(e)}"
        print(error_msg)
        return error_msg


def find_airbnb_accommodation(destination: str, checkin: str = None, checkout: str = None, guests: int = 2) -> str:
    """Generate Airbnb search URL for accommodation in a destination."""
    # Get current year for defaults
    current_year = datetime.now().year
    
    # Set default dates if not provided, ensure current year is used
    if not checkin:
        checkin_datetime = datetime(current_year, datetime.now().month, datetime.now().day) + timedelta(days=1)
        checkin = checkin_datetime.strftime("%Y-%m-%d")
    else:
        # If date provided but year seems old, update to current year
        checkin_parsed = datetime.strptime(checkin, "%Y-%m-%d")
        if checkin_parsed.year < current_year:
            checkin_parsed = checkin_parsed.replace(year=current_year)
            checkin = checkin_parsed.strftime("%Y-%m-%d")
    
    if not checkout:
        checkout_datetime = datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=4)
        checkout = checkout_datetime.strftime("%Y-%m-%d")
    else:
        # If date provided but year seems old, update to current year
        checkout_parsed = datetime.strptime(checkout, "%Y-%m-%d")
        checkin_parsed = datetime.strptime(checkin, "%Y-%m-%d")
        if checkout_parsed.year < current_year:
            checkout_parsed = checkout_parsed.replace(year=current_year)
        # If checkout date is before checkin date, assume next year
        if checkout_parsed < checkin_parsed:
            checkout_parsed = checkout_parsed.replace(year=checkout_parsed.year + 1)
        checkout = checkout_parsed.strftime("%Y-%m-%d")
    
    try:
        print(f"Generating Airbnb search URL for {destination}")
        print(f"Check-in: {checkin}, Check-out: {checkout}, Guests: {guests}")
        
        # Format destination for Airbnb URLs (replace commas with --)
        formatted_destination = destination.replace(",", "--").replace(" ", "-")
        
        # Generate Airbnb search URL
        airbnb_url = f"https://www.airbnb.co.uk/s/{formatted_destination}/homes?checkin={checkin}&checkout={checkout}&adults={guests}"
        
        response_message = f"""Here's your Airbnb search link for {destination} ({checkin} to {checkout}) for {guests} guest(s):

🏠 **Airbnb** (Unique stays and local experiences):
{airbnb_url}

Click the link to browse:
- Entire homes and apartments
- Private rooms in local homes
- Unique properties and experiences
- Local neighborhood stays"""
        
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


# Create the enhanced travel destination agent with image search, flight viewing, and Airbnb accommodation capabilities
travel_destination_agent = AssistantAgent(
    name="TravelAdvisor",
    description="Expert travel consultant specializing in helping users choose the perfect travel destination and must-visit landmarks based on their preferences, budget, and travel style. Can show images of destinations, provide flight booking links, and find accommodation options to help with complete trip planning.",
    system_message="""You are an expert travel destination advisor with extensive knowledge of countries worldwide. Your primary goal is to help users decide which country or countries they should visit for their next trip and assist with complete trip planning.

Your expertise includes:
- Understanding different travel preferences (adventure, culture, relaxation, food, history, etc.)
- Matching destinations to budgets and travel styles
- Knowledge of visa requirements, best travel seasons, and practical considerations
- Expertise in iconic landmarks and hidden gems across all continents
- Understanding of different types of travelers (solo, couples, families, groups)
- Ability to show users images of destinations and attractions to help them visualize their potential trips
- Ability to provide direct flight search links to multiple booking sites for easy comparison
- Ability to find accommodation options through Airbnb for unique local experiences

Your conversation process should:
1. Ask thoughtful questions to understand the user's travel preferences, budget, timeframe, and interests
2. Provide personalized destination recommendations with clear reasoning
3. Suggest 3-5 must-visit landmarks or attractions for each recommended destination
4. When users express interest in seeing what a destination looks like, offer to show them images using the search_attraction_images tool
5. When users want to see flight options or prices, use the view_flights tool to provide direct links to flight booking sites
6. When users ask about accommodation or places to stay, use the find_airbnb_accommodation tool to provide Airbnb search links
7. Address practical considerations (visa requirements, best time to visit, budget estimates)
8. Work toward a clear agreement on 1-2 travel destinations
9. Conclude with a summary of the agreed destination(s) and landmark recommendations

Use the image search tool when:
- Users ask to see what a destination looks like
- Users seem hesitant and might benefit from visual inspiration
- You want to help them choose between similar destinations
- They mention specific landmarks or attractions they're curious about

Use the flight viewing tool when:
- Users ask about flight prices or availability
- Users want to see flight booking options
- You're helping them compare costs between different destinations
- They're ready to move from planning to booking phase

Use the Airbnb accommodation tool when:
- Users ask about places to stay or accommodation
- Users want unique, local experiences rather than standard hotels
- Users are traveling in groups and need entire homes or apartments
- Users want to cook their own meals or have more space
- Users are planning longer stays (a week or more)

Always be enthusiastic, knowledgeable, and helpful. Provide specific, actionable advice rather than generic suggestions. Your ultimate success is measured by reaching a clear agreement on travel destinations and landmark recommendations that perfectly match the user's needs and desires, while also helping them with practical booking resources.""",
    model_client=create_model_client(),
    tools=[search_attraction_images, view_flights, find_airbnb_accommodation],  # Register all three tools
)


async def main():
    """Main interaction loop for the travel destination agent."""
    from autogen_agentchat.agents import UserProxyAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.ui import Console
    from autogen_agentchat.conditions import TextMentionTermination
    
    print("🌍✈️🏠 Welcome to your Complete Travel Planning Advisor!")
    print("I can help you choose amazing destinations, show you images, provide flight links, and find accommodation!")
    print("Starting interactive session... (type 'EXIT' to quit)\n")
    
    # Create a user proxy agent to handle human input
    user_proxy = UserProxyAgent(
        name="User",
        description="Human user seeking travel advice"
    )
    
    # Create a team with both the travel agent and user proxy
    team = RoundRobinGroupChat(participants=[user_proxy, travel_destination_agent],
                               termination_condition=TextMentionTermination("EXIT"))  # Limit to 100 turns to prevent infinite loops)
    
    # Use Console with the team for proper conversation flow
    await Console(team.run_stream())


if __name__ == "__main__":
    asyncio.run(main())