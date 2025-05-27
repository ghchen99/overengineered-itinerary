import os
import asyncio
from datetime import datetime
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

def create_model_client():
    """Create and return the Azure OpenAI model client."""
    return AzureOpenAIChatCompletionClient(
        model = os.environ["AZURE_OPENAI_MODEL_NAME"],
        azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

async def retrieve_flights(from_location: str, to_location: str, depart_date: str, return_date: str):
    """
    Retrieve flight information for the specified route and dates.
    
    Args:
        from_location (str): Origin city/airport
        to_location (str): Destination city/airport  
        depart_date (str): Departure date in YYYY-MM-DD format
        return_date (str): Return date in YYYY-MM-DD format
    
    Returns:
        Flight search results
    """
    # Create web surfer with optimized settings
    web_surfer_agent = MultimodalWebSurfer(
        name="FlightSearchAgent",
        model_client=create_model_client(),
        headless=False,  # Run headless for better performance
        description="Extract flight data from Kayak as JSON ONLY.",
        # Use Kayak URL with pre-filled parameters
        start_page=f"https://www.kayak.co.uk/flights/{from_location}-{to_location}/{depart_date}/{return_date}?sort=bestflight_a"
    )

    # Ultra-efficient - maximum 5 turns for scrolling and data collection
    agent_team = RoundRobinGroupChat([web_surfer_agent], max_turns=5)

    # Updated task with cookie rejection and scrolling
    flight_search_task = f"""
    Extract flight data efficiently. Steps:
    1. If cookie banner appears, reject cookies
    2. Scroll once to load additional flights
    3. Extract all visible flight information

    Return JSON format:
    {{
      "search_params": {{
        "from": "{from_location}",
        "to": "{to_location}",
        "depart_date": "{depart_date}",
        "return_date": "{return_date}"
      }},
      "flights": [
        {{
          "option_number": 1,
          "outbound": {{
            "departure_time": "HH:MM",
            "arrival_time": "HH:MM",
            "airline": "Airline Name",
            "duration": "Xh XXm",
            "stops": "Nonstop/1 stop/etc"
          }},
          "return": {{
            "departure_time": "HH:MM",
            "arrival_time": "HH:MM",
            "airline": "Airline Name", 
            "duration": "Xh XXm",
            "stops": "Nonstop/1 stop/etc"
          }},
          "total_price": "£XXX"
        }}
      ]
    }}
    ```

    IMPORTANT INSTRUCTIONS:
    - REJECT cookies first thing
    - Scroll down slowly 2-3 times to load additional flights
    - Extract data for ALL visible flights after scrolling
    - Include flight number/option position
    - NO text explanations or summaries
    - START response with ```json and END with ```
    - If no flights found, return empty array but keep the JSON structure
    """

    try:
        # Run the team
        stream = agent_team.run_stream(task=flight_search_task)
        await Console(stream)
    finally:
        # Ensure browser is closed
        await web_surfer_agent.close()

async def main() -> None:
    """Main function to demonstrate flight retrieval."""
    # Example usage with airport codes for Kayak
    today = datetime.now().strftime("%Y-%m-%d")
    return_date = "2025-06-05"
    
    await retrieve_flights(
        from_location="LHR",  # London Heathrow
        to_location="HKG",    # Hong Kong  
        depart_date=today,
        return_date=return_date
    )

if __name__ == "__main__":
    asyncio.run(main())