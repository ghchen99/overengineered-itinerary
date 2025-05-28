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


def search_attraction_images(attraction_name: str) -> str:
    """Search for attraction images on Google Images and scroll through results."""
    driver = None
    try:
        print(f"Searching for images of: {attraction_name}")
        driver = setup_chrome_driver()
        
        # Navigate to Google Images
        driver.get("https://images.google.com")
        time.sleep(2)
        
        # Handle cookie consent
        handle_cookie_consent(driver)
        
        # Find search box and enter query
        print("Entering search query...")
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(attraction_name)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load
        print("Waiting for search results...")
        time.sleep(4)
        
        # Perform slow scroll through images
        perform_slow_scroll(driver)
        
        print("Waiting for 2 seconds before closing...")
        time.sleep(2)
        
        return f"Successfully displayed images of {attraction_name}. The browser showed various photos to help visualize this destination."
        
    except Exception as e:
        error_msg = f"Error searching for images of {attraction_name}: {str(e)}"
        print(error_msg)
        return error_msg
    
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed successfully.")
            except:
                print("Browser was already closed.")


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
        
        # URL encode the destination
        encoded_destination = urllib.parse.quote(destination)
        
        # Generate Airbnb search URL
        airbnb_url = f"https://www.airbnb.co.uk/s/{encoded_destination}/homes?checkin={checkin}&checkout={checkout}&adults={guests}"
        
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
    
    # Images Agent - Shows visual content of attractions
    images_agent = AssistantAgent(
        name="ImagesAgent",
        description="Specializes in showing visual content of travel destinations and attractions.",
        system_message="""You are a visual content specialist for travel planning.
Your job is to show images of destinations, attractions, and landmarks to help travelers visualize their trip.

When directed to show images:
1. Use the search_attraction_images tool to display visual content
2. Focus on the specific attraction, landmark, or destination mentioned
3. Provide brief context about what the images show
4. Help travelers get excited about their potential destination

Always use the search_attraction_images tool when asked to show visual content.
Keep your responses concise and focused on the visual experience.""",
        model_client=model_client,
        tools=[search_attraction_images],
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
        if last_message.source in ["ImagesAgent", "FlightsAgent", "AccommodationAgent"]:
            return "TravelSupervisor"
        
        # Let LLM decide when supervisor was last to speak
        return None
    
    supervisor_agent = AssistantAgent(
        name="TravelSupervisor",
        description="Travel planning supervisor coordinating specialized agents.",
        system_message="""You are a travel planning supervisor managing a team of specialized agents.
Your job is to coordinate the team to provide comprehensive travel assistance.

Use these specific instruction formats:

1. For showing images: "@ImagesAgent: show images of [specific attraction/destination]"
2. For flights: "@FlightsAgent: find flights from [origin] to [destination] departing [date] returning [date]"  
3. For accommodation: "@AccommodationAgent: find Airbnb accommodation in [destination] from [checkin] to [checkout] for [guests] guests"

Your workflow:
1. Understand the user's travel request (destination, dates, preferences)
2. Direct ImagesAgent to show visual content of key attractions
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
        participants=[supervisor_agent, images_agent, flights_agent, accommodation_agent],
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
    I want to plan a trip to Tokyo, Japan for 7 days in October. 
    I'll be traveling from London (LHR). I'm interested in seeing temples, 
    trying authentic Japanese food, and experiencing the city culture.
    I need help with flights, accommodation, and I'd love to see what some 
    of the main attractions look like. My budget is flexible.
    """
    
    await run_travel_planner(travel_request)


if __name__ == "__main__":
    asyncio.run(main())