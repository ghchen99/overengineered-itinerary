import os
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import BaseChatMessage, BaseAgentEvent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from datetime import datetime, timedelta
import urllib.parse
from typing import Sequence, Optional


def setup_chrome_driver():
    """Set up Chrome driver with common options for web automation."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def handle_cookie_consent(driver):
    """Handle cookie consent popups commonly found on websites."""
    print("Looking for cookie consent popup...")
    
    reject_selectors = [
        "//button[contains(text(), 'Reject all')]",
        "//button[contains(text(), 'I disagree')]", 
        "//div[contains(text(), 'Reject all')]//ancestor::button",
        "//button[@aria-label='Reject all']",
        "//button[.//div[contains(text(), 'Reject all')]]",
        "[data-testid='uc-reject-all-button']",
        "//div[text()='Reject all']/parent::button"
    ]
    
    for selector in reject_selectors:
        try:
            reject_button = driver.find_element(By.XPATH, selector)
            if reject_button.is_displayed():
                driver.execute_script("arguments[0].click();", reject_button)
                print("Rejected cookies successfully")
                time.sleep(2)
                return True
        except:
            continue
    
    print("No cookie popup found - continuing...")
    return False


def perform_slow_scroll(driver, max_scrolls=4, scroll_increment=500, scroll_pause_time=2.5):
    """Perform slow, smooth scrolling to view content on a webpage."""
    print(f"Starting slow scroll through content...")
    
    for scroll_count in range(max_scrolls):
        print(f"Scroll {scroll_count + 1}/{max_scrolls}")
        
        current_scroll = driver.execute_script("return window.pageYOffset;")
        
        driver.execute_script(f"""
            window.scrollTo({{
                top: {current_scroll + scroll_increment},
                behavior: 'smooth'
            }});
        """)
        
        time.sleep(scroll_pause_time)
        
        # Try to load more content if available
        try:
            load_more_elements = driver.find_elements(By.CSS_SELECTOR, 
                "input[value='Show more results'], [jsaction*='more'], .mye4qd")
            if load_more_elements:
                for element in load_more_elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        print("Loading more content...")
                        time.sleep(2)
                        break
        except:
            pass
    
    print(f"Scrolling completed after {max_scrolls} scrolls.")


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

        response_message = f"""Here are flight search links for {from_location} to {to_location} ({depart_date} to {return_date}):

🔗 **Kayak** (Best for comparing prices):
{kayak_url}

🔗 **Skyscanner** (Good for flexible dates):
{skyscanner_url}

Click these links to view current flight options, prices, and availability."""
        
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


def create_travel_supervisor_team(model_client):
    """Create a supervisor-managed team of travel specialists."""
    
    # Itinerary Agent - Creates detailed day-by-day schedules and city recommendations
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Specializes in creating detailed day-by-day itineraries and recommending cities to stay in.",
        system_message="""You are an expert itinerary planner and city recommendation specialist.
Your job is to create detailed day-by-day schedules and recommend the best cities/areas to stay in for travelers.

When directed to create an itinerary:
1. Recommend optimal cities/neighborhoods to base yourself in
2. Create realistic daily schedules with morning, afternoon, and evening activities
3. Consider travel logistics between different areas
4. Balance must-see attractions with authentic local experiences
5. Provide practical tips for navigation and booking
6. Consider the traveler's interests, budget, and travel style

Your itineraries should include:
- Strategic city/area recommendations for accommodation
- Day-by-day detailed schedules
- Transportation advice between locations
- Booking tips and advance planning needs
- Mix of popular attractions and hidden gems
- Cultural experiences and local food recommendations

Format your response with:
🗺️ **DETAILED [X]-DAY ITINERARY FOR [DESTINATION]**
📍 **Recommended Cities/Areas to Stay**
📅 **DAY-BY-DAY SCHEDULE**
💡 **TRAVEL TIPS**

Keep recommendations practical, well-organized, and tailored to the specific destination and traveler preferences.""",
        model_client=model_client,
    )
    
    # Flights Agent - Provides flight booking links
    flights_agent = AssistantAgent(
        name="FlightsAgent", 
        description="Specializes in providing flight booking links and flight information.",
        system_message="""You are a flight booking specialist.
Your job is to provide flight booking links and flight information.

When directed to find flights:
1. Use the view_flights tool to generate booking links
2. Include origin, destination, and travel dates
3. Provide links to multiple booking sites for comparison
4. Give brief tips about booking timing and airline options

Always use the view_flights tool when asked about flights.
Focus on providing actionable booking links rather than general advice.""",
        model_client=model_client,
        tools=[view_flights],
    )
    
    # Accommodation Agent - Provides Airbnb links
    accommodation_agent = AssistantAgent(
        name="AccommodationAgent",
        description="Specializes in providing Airbnb accommodation links and lodging information.",
        system_message="""You are an accommodation specialist focusing on Airbnb rentals.
Your job is to provide Airbnb booking links and accommodation recommendations.

When directed to find accommodation:
1. Use the find_airbnb_accommodation tool to generate Airbnb search links
2. Include destination, check-in/out dates, and number of guests
3. Provide context about different types of Airbnb stays available
4. Mention benefits of Airbnb for the specific destination

Always use the find_airbnb_accommodation tool when asked about accommodation.
Focus on providing actionable booking links and practical lodging advice.""",
        model_client=model_client,
        tools=[find_airbnb_accommodation],
    )
    
    # Supervisor Agent - Coordinates the team
    def supervisor_selector(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> Optional[str]:
        """Custom selector ensuring supervisor coordinates after specialist responses."""
        if not messages:
            return "TravelSupervisor"  # Start with supervisor
        
        last_message = messages[-1]
        # Return to supervisor after any specialist agent responds
        if last_message.source in ["ItineraryAgent", "FlightsAgent", "AccommodationAgent"]:
            return "TravelSupervisor"
        
        # Let LLM decide when supervisor was last to speak
        return None
    
    supervisor_agent = AssistantAgent(
        name="TravelSupervisor",
        description="Travel planning supervisor coordinating specialized agents.",
        system_message="""You are a travel planning supervisor managing a team of specialized agents.
Your job is to coordinate the team to provide comprehensive travel assistance.

Use these specific instruction formats:

1. For creating itinerary: "@ItineraryAgent: create an itinerary for the trip to [specific attraction/destination] for [duration] days."
2. For flights: "@FlightsAgent: find flights from [origin] to [destination] departing [date] returning [date]"  
3. For accommodation: "@AccommodationAgent: find Airbnb accommodation in [destination] from [checkin] to [checkout] for [guests] guests"

Your workflow:
1. Understand the user's travel request (destination, dates, preferences)
2. Direct ItineraryAgent to show visual content of key attractions
3. Direct FlightsAgent to provide flight booking links
4. Direct AccommodationAgent to provide Airbnb accommodation links
5. Synthesize all information into a cohesive travel plan
6. Provide practical next steps for booking

Always be specific with dates, locations, and requirements when directing agents.
End your final response with "TRAVEL PLANNING COMPLETE" when finished.""",
        model_client=model_client,
    )
    
    # Termination condition
    termination = TextMentionTermination("TRAVEL PLANNING COMPLETE") | MaxMessageTermination(30)
    
    # Create supervisor team
    team = SelectorGroupChat(
        participants=[supervisor_agent, itinerary_agent, flights_agent, accommodation_agent],
        model_client=model_client,
        termination_condition=termination,
        selector_func=supervisor_selector,
    )
    
    return team


async def run_travel_planner(travel_request: str):
    """Run the travel planner with supervisor pattern."""
    print(f"\n{'='*80}\nRunning Travel Planner with Supervisor Pattern\n{'='*80}\n")
    
    model_client = create_model_client()
    
    try:
        # Create the supervisor team
        team = create_travel_supervisor_team(model_client)
        
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
    I need help with flights, accommodation, and I'd love to see what some 
    of the main attractions look like. My budget is flexible.
    """
    
    await run_travel_planner(travel_request)


if __name__ == "__main__":
    asyncio.run(main())