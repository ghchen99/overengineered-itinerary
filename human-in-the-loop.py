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
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from datetime import datetime, timedelta
import urllib.parse


def setup_chrome_driver():
    """
    Set up Chrome driver with common options for web automation.
    
    Returns:
        webdriver.Chrome: Configured Chrome driver instance
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def handle_cookie_consent(driver):
    """
    Handle cookie consent popups commonly found on websites.
    
    Args:
        driver: Selenium webdriver instance
        
    Returns:
        bool: True if cookie popup was handled, False otherwise
    """
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
    """
    Perform slow, smooth scrolling to view content on a webpage.
    
    Args:
        driver: Selenium webdriver instance
        max_scrolls (int): Maximum number of scrolls to perform
        scroll_increment (int): Pixels to scroll each time
        scroll_pause_time (float): Seconds to pause between scrolls
    """
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
        
        # Try to load more content if available (for images)
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
    """
    Search for an attraction on Google Images and slowly scroll through results.
    This tool helps users visualize destinations and landmarks they're considering.
    
    Args:
        attraction_name (str): Name of the attraction or destination to search for
    
    Returns:
        str: Status message about the image search operation
    """
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
        
        return f"Successfully displayed images of {attraction_name}. The browser showed various photos and views of this destination to help you visualize what it looks like."
        
    except Exception as e:
        error_msg = f"An error occurred while searching for images of {attraction_name}: {str(e)}"
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
    
    print("🌍✈️🏠 Welcome to your Complete Travel Planning Advisor!")
    print("I can help you choose amazing destinations, show you images, provide flight links, and find accommodation!")
    print("Starting interactive session... (type 'TERMINATE' to quit)\n")
    
    # Create a user proxy agent to handle human input
    user_proxy = UserProxyAgent(
        name="User",
        description="Human user seeking travel advice"
    )
    
    # Create a team with both the travel agent and user proxy
    team = RoundRobinGroupChat([user_proxy, travel_destination_agent])
    
    # Use Console with the team for proper conversation flow
    await Console(team.run_stream())


if __name__ == "__main__":
    # You can test individual functions:
    # result = search_attraction_images("Eiffel Tower")
    # print(result)
    # 
    # result = view_flights("LHR", "HKG", "2025-07-01", "2025-07-10")
    # print(result)
    #
    # result = find_airbnb_accommodation("Paris", "2025-07-01", "2025-07-08", 4)
    # print(result)
    
    # Run the main agent interaction
    asyncio.run(main())