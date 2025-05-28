import os
import asyncio
import argparse
from enum import Enum
from typing import Sequence, Optional

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import BaseChatMessage, BaseAgentEvent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Define agent pattern enum
class AgentPattern(str, Enum):
    SEQUENTIAL = "sequential"
    NETWORK = "network"
    SUPERVISOR = "supervisor"

def create_model_client():
    """Create and return the Azure OpenAI model client."""
    return AzureOpenAIChatCompletionClient(
        model = os.environ["AZURE_OPENAI_MODEL_NAME"],
        azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

def create_sequential_team(model_client):
    """Create a sequential team of specialized travel planning agents."""
    # Create specialized travel research agents
    flights_agent = AssistantAgent(
        name="FlightsAgent",
        description="Specializes in researching and recommending flight options.",
        system_message="""You are a flight booking specialist.
Your job is to recommend flight options based on the user's travel request.

When asked about flights, provide:
1. 3-5 flight options with different airlines, considering:
   - Direct flights vs. connections
   - Departure/arrival times
   - Price ranges
   - Airline quality and reputation
2. Information about baggage allowances and policies
3. Tips for the best time to book flights for this route
4. Any potential travel restrictions or visa requirements

Format your recommendations clearly with departure/arrival times, total flight duration,
number of connections, and price estimates.

You don't have real-time access to actual flight search engines, but you should provide realistic
flight options based on common carriers, typical prices, and routes for the requested journey.""",
        model_client=model_client,
    )
    
    accommodations_agent = AssistantAgent(
        name="AccommodationsAgent",
        description="Specializes in researching and recommending accommodation options.",
        system_message="""You are an accommodation specialist.
Your job is to recommend lodging options based on the user's travel request and budget.

When asked about accommodations, provide:
1. 3-5 accommodation options in different neighborhoods/areas, considering:
   - Location and proximity to attractions
   - Price ranges fitting the user's budget
   - Type of accommodation (hotel, hostel, apartment)
   - Amenities and services offered
2. Tips for the best neighborhoods to stay in
3. Information about local transportation options from each area

Format your recommendations clearly with location details, price ranges per night,
notable amenities, and nearby attractions or transportation.

You don't have real-time access to booking sites, but you should provide realistic
accommodation options based on common hotels, hostels, and rental properties in the destination.""",
        model_client=model_client,
    )

    attractions_agent = AssistantAgent(
        name="AttractionsAgent",
        description="Specializes in researching and recommending attractions and activities.",
        system_message="""You are an attractions and activities specialist.
Your job is to recommend things to do and see based on the user's interests and destination.

When asked about attractions, provide:
1. 10-15 key attractions and activities organized by type:
   - Major landmarks and monuments
   - Museums and cultural sites
   - Local experiences (markets, neighborhoods)
   - Food and dining recommendations
   - Day trips if applicable
2. For each attraction, include:
   - Brief description
   - Estimated visit time
   - Approximate entrance fees if applicable
   - Tips for best times to visit
   - Relevant historical or cultural context

Format your recommendations by categories and include practical visiting information.

You don't have real-time access to attraction websites, but you should provide accurate
and realistic information about well-known attractions and local experiences.""",
        model_client=model_client,
    )
    
    research_agent = AssistantAgent(
        name="ResearchAgent",
        description="Analyzes information from specialist agents and requests specific details.",
        system_message="""You are a travel research coordinator in a sequential team workflow.
Your job is to request specific information from each specialist agent and analyze their responses.

WORKFLOW INSTRUCTIONS:
1. First, request FlightsAgent to provide flight options between the specified origin and destination.
2. After flights are analyzed, request AccommodationsAgent to provide accommodation options based on the travel dates.
3. Then, request AttractionsAgent to provide attraction and activity recommendations at the destination.
4. Analyze all information and compile key points for travel planning.

For each specialist agent, provide clear instructions including:
- For flights: specific origin, destination, dates, and preferences
- For accommodations: location, check-in/out dates, budget, and amenities preferences
- For attractions: specific types of attractions, locations, and interests mentioned

Extract and organize key information from all responses including:
- Flight options with prices, times, and airlines
- Accommodation options with locations, prices, and amenities
- Attraction details with opening hours, admission fees, and visitor recommendations

Pass this organized information to the ItineraryAgent for final planning.""",
        model_client=model_client,
    )
    
    itinerary_agent = AssistantAgent(
        name="ItineraryAgent",
        description="Creates a detailed day-by-day itinerary for the trip based on research.",
        system_message="""You are an itinerary planning agent, the final agent in a sequential team workflow.
Your job is to create a comprehensive travel plan based on the research provided by previous agents.

When creating the travel plan, include:
1. A summary of selected flights with departure/arrival times and prices
2. Details of chosen accommodation with location, amenities, and total cost
3. A detailed day-by-day itinerary including:
   - Attractions to visit each day with opening hours and admission fees
   - Estimated travel times between locations and recommended transportation
   - Meal recommendations including local cuisine options and estimated costs
   - Flexible time blocks for rest or additional exploration
4. A complete budget breakdown showing:
   - Transportation costs (flights, local transit)
   - Accommodation costs
   - Daily food and activity expenses
   - Contingency funds

Format your plan in a clear, organized manner with headings and sections.
Consider the traveler's stated interests, budget constraints, and practical logistics.
Ensure the itinerary balances activities with reasonable travel times and rest periods.

End your final response with "PLANNING COMPLETE" when the comprehensive travel plan is finished.""",
        model_client=model_client,
    )
    
    # The termination condition
    termination = TextMentionTermination("PLANNING COMPLETE") | MaxMessageTermination(40)
    
    # Create a sequential (round robin) team with the specialized agents
    team = RoundRobinGroupChat(
        participants=[research_agent, flights_agent, accommodations_agent, attractions_agent, itinerary_agent],
        termination_condition=termination,
    )
    
    return team

def create_network_team(model_client):
    """Create a network/mesh team of specialized travel planning agents."""
    # Create specialized travel agents
    flights_agent = AssistantAgent(
        name="FlightsAgent",
        description="Specializes in researching and recommending flight options.",
        system_message="""You are a flight booking specialist.
Your job is to recommend flight options based on the user's travel request.

When asked about flights, provide:
1. 3-5 flight options with different airlines, considering:
   - Direct flights vs. connections
   - Departure/arrival times
   - Price ranges
   - Airline quality and reputation
2. Information about baggage allowances and policies
3. Tips for the best time to book flights for this route
4. Any potential travel restrictions or visa requirements

Format your recommendations clearly with departure/arrival times, total flight duration,
number of connections, and price estimates.

You don't have real-time access to actual flight search engines, but you should provide realistic
flight options based on common carriers, typical prices, and routes for the requested journey.""",
        model_client=model_client,
    )
    
    hotels_agent = AssistantAgent(
        name="HotelsAgent",
        description="Specializes in researching and recommending hotel options.",
        system_message="""You are a hotel specialist.
Your job is to recommend hotel accommodations based on the user's travel request and budget.

When asked about hotels, provide:
1. 3-5 hotel options in different price ranges, considering:
   - Location and proximity to attractions
   - Price ranges fitting the user's budget
   - Star ratings and quality
   - Amenities and services offered (breakfast, pool, wifi)
2. Tips for the best hotel districts to stay in
3. Information about local transportation options from each hotel

Format your recommendations clearly with location details, price ranges per night,
notable amenities, and nearby attractions or transportation.

You don't have real-time access to booking sites, but you should provide realistic
hotel options based on well-known properties in the destination.""",
        model_client=model_client,
    )
    
    alternative_stays_agent = AssistantAgent(
        name="AlternativeStaysAgent",
        description="Specializes in researching and recommending vacation rentals and alternative accommodations.",
        system_message="""You are a vacation rental and alternative accommodations specialist.
Your job is to recommend non-hotel lodging options based on the user's travel request and budget.

When asked about alternative accommodations, provide:
1. 3-5 rental options in different neighborhoods, considering:
   - Location and proximity to attractions
   - Price ranges fitting the user's budget
   - Type of accommodation (apartment, house, hostel, B&B)
   - Space and amenities offered (kitchen, laundry, living space)
2. Tips for the best neighborhoods for rentals
3. Information about local transportation options from each area

Format your recommendations clearly with location details, price ranges per night,
notable amenities, and nearby attractions or transportation.

You don't have real-time access to booking sites, but you should provide realistic
rental options based on common availability in the destination.""",
        model_client=model_client,
    )

    attractions_agent = AssistantAgent(
        name="AttractionsAgent",
        description="Specializes in researching and recommending attractions and activities.",
        system_message="""You are an attractions and activities specialist.
Your job is to recommend things to do and see based on the user's interests and destination.

When asked about attractions, provide:
1. 10-15 key attractions and activities organized by type:
   - Major landmarks and monuments
   - Museums and cultural sites
   - Local experiences (markets, neighborhoods)
   - Food and dining recommendations
   - Day trips if applicable
2. For each attraction, include:
   - Brief description
   - Estimated visit time
   - Approximate entrance fees if applicable
   - Tips for best times to visit
   - Relevant historical or cultural context

Format your recommendations by categories and include practical visiting information.

You don't have real-time access to attraction websites, but you should provide accurate
and realistic information about well-known attractions and local experiences.""",
        model_client=model_client,
    )
    
    planning_agent = AssistantAgent(
        name="PlanningAgent",
        description="Synthesizes information to create a comprehensive travel plan.",
        system_message="""You are a travel planning specialist.
Your job is to synthesize information from all specialist agents to create a comprehensive travel plan.

Direct each specialist agent to provide specific information in their domain:
- Direct FlightsAgent to recommend flight options between the specified origin and destination
- Direct HotelsAgent to recommend hotel options in the destination
- Direct AlternativeStaysAgent to recommend rental options in the destination
- Direct AttractionsAgent to recommend attractions and activities based on interests

Create a day-by-day itinerary incorporating all the gathered information.
When requesting information, be extremely specific with your requirements.

End your final response with "PLANNING COMPLETE" when the travel plan is finished.""",
        model_client=model_client,
    )
    
    # The termination condition
    termination = TextMentionTermination("PLANNING COMPLETE") | MaxMessageTermination(40)
    
    # Create a selector-based team
    team = SelectorGroupChat(
        participants=[flights_agent, hotels_agent, attractions_agent, alternative_stays_agent, planning_agent],
        model_client=model_client,  # For agent selection
        termination_condition=termination,
    )
    
    return team

def create_supervisor_team(model_client):
    """Create a hierarchical team with a supervisor managing multiple specialized agents."""
    # Create specialized travel agents
    flights_agent = AssistantAgent(
        name="FlightsAgent",
        description="Specializes in researching and recommending flight options.",
        system_message="""You are a flight booking specialist.
Your job is to recommend flight options based on the user's travel request.

When asked about flights, provide:
1. 3-5 flight options with different airlines, considering:
   - Direct flights vs. connections
   - Departure/arrival times
   - Price ranges
   - Airline quality and reputation
2. Information about baggage allowances and policies
3. Tips for the best time to book flights for this route
4. Any potential travel restrictions or visa requirements

Format your recommendations clearly with departure/arrival times, total flight duration,
number of connections, and price estimates.

You don't have real-time access to actual flight search engines, but you should provide realistic
flight options based on common carriers, typical prices, and routes for the requested journey.""",
        model_client=model_client,
    )
    
    hotels_agent = AssistantAgent(
        name="HotelsAgent",
        description="Specializes in researching and recommending hotel options.",
        system_message="""You are a hotel specialist.
Your job is to recommend hotel accommodations based on the user's travel request and budget.

When asked about hotels, provide:
1. 3-5 hotel options in different price ranges, considering:
   - Location and proximity to attractions
   - Price ranges fitting the user's budget
   - Star ratings and quality
   - Amenities and services offered (breakfast, pool, wifi)
2. Tips for the best hotel districts to stay in
3. Information about local transportation options from each hotel

Format your recommendations clearly with location details, price ranges per night,
notable amenities, and nearby attractions or transportation.

You don't have real-time access to booking sites, but you should provide realistic
hotel options based on well-known properties in the destination.""",
        model_client=model_client,
    )
    
    alternative_stays_agent = AssistantAgent(
        name="AlternativeStaysAgent",
        description="Specializes in researching and recommending vacation rentals and alternative accommodations.",
        system_message="""You are a vacation rental and alternative accommodations specialist.
Your job is to recommend non-hotel lodging options based on the user's travel request and budget.

When asked about alternative accommodations, provide:
1. 3-5 rental options in different neighborhoods, considering:
   - Location and proximity to attractions
   - Price ranges fitting the user's budget
   - Type of accommodation (apartment, house, hostel, B&B)
   - Space and amenities offered (kitchen, laundry, living space)
2. Tips for the best neighborhoods for rentals
3. Information about local transportation options from each area

Format your recommendations clearly with location details, price ranges per night,
notable amenities, and nearby attractions or transportation.

You don't have real-time access to booking sites, but you should provide realistic
rental options based on common availability in the destination.""",
        model_client=model_client,
    )

    attractions_agent = AssistantAgent(
        name="AttractionsAgent",
        description="Specializes in researching and recommending attractions and activities.",
        system_message="""You are an attractions and activities specialist.
Your job is to recommend things to do and see based on the user's interests and destination.

When asked about attractions, provide:
1. 10-15 key attractions and activities organized by type:
   - Major landmarks and monuments
   - Museums and cultural sites
   - Local experiences (markets, neighborhoods)
   - Food and dining recommendations
   - Day trips if applicable
2. For each attraction, include:
   - Brief description
   - Estimated visit time
   - Approximate entrance fees if applicable
   - Tips for best times to visit
   - Relevant historical or cultural context

Format your recommendations by categories and include practical visiting information.

You don't have real-time access to attraction websites, but you should provide accurate
and realistic information about well-known attractions and local experiences.""",
        model_client=model_client,
    )
    
    def supervisor_selector(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> Optional[str]:
        """Custom selector that ensures the supervisor is called after specialist agent responses."""
        if not messages:
            return "TravelSupervisor"  # Start with supervisor
        
        last_message = messages[-1]
        # If the last message was from any specialist agent, go back to supervisor
        if last_message.source in ["FlightsAgent", "HotelsAgent", "AlternativeStaysAgent", "AttractionsAgent"]:
            return "TravelSupervisor"
        
        # If the last message was from the supervisor, let the LLM decide
        # (most likely will choose one of the specialist agents for the next action)
        return None
    
    supervisor_agent = AssistantAgent(
        name="TravelSupervisor",
        description="Travel planning supervisor that directs multiple specialized agents.",
        system_message="""You are a travel planning supervisor managing a team of specialized agents.
Use these explicit instruction formats when directing each agent:

1. For flights: "@FlightsAgent: recommend flight options from [origin] to [destination] on [specific dates]"

2. For hotels: "@HotelsAgent: recommend hotels in [location] for [specific dates] with [price range]"

3. For alternative stays: "@AlternativeStaysAgent: recommend rentals in [location] for [specific dates] with [preferences]"

4. For attractions: "@AttractionsAgent: recommend [specific attraction type] in [location]"

Coordinate the team by:
1. First requesting flight recommendations to establish travel dates
2. Then requesting accommodation options based on confirmed travel dates
3. Finally requesting attraction and activity recommendations for each day
4. Create a comprehensive itinerary based on all information gathered

End your final response with "PLANNING COMPLETE" when the travel plan is finished.""",
        model_client=model_client,
    )
    
    # The termination condition
    termination = TextMentionTermination("PLANNING COMPLETE") | MaxMessageTermination(40)
    
    # Create a selector-based team with a custom selector function
    team = SelectorGroupChat(
        participants=[supervisor_agent, flights_agent, hotels_agent, alternative_stays_agent, attractions_agent],
        model_client=model_client,  # For agent selection
        termination_condition=termination,
        selector_func=supervisor_selector,
    )
    
    return team

async def run_travel_planner(pattern: AgentPattern, travel_request: str):
    """Run the travel planner using the specified pattern."""
    print(f"\n{'='*80}\nRunning travel planner with {pattern.value} pattern\n{'='*80}\n")
    
    model_client = create_model_client()
    
    try:
        # Create the appropriate team based on the pattern
        if pattern == AgentPattern.SEQUENTIAL:
            team = create_sequential_team(model_client)
        elif pattern == AgentPattern.NETWORK:
            team = create_network_team(model_client)
        elif pattern == AgentPattern.SUPERVISOR:
            team = create_supervisor_team(model_client)
        
        # Run the team with the travel request
        stream = team.run_stream(task=travel_request)
        
        # Display the conversation in the console
        await Console(stream)
    finally:
        # Close model client connections
        await model_client.close()

async def main():
    """Main function to run the travel planner."""
    parser = argparse.ArgumentParser(description="Multi-Agent Travel Planner")
    parser.add_argument(
        "--pattern", 
        type=AgentPattern, 
        choices=list(AgentPattern), 
        default=AgentPattern.SEQUENTIAL,
        help="Agent pattern to use (sequential, network, or supervisor)"
    )
    
    args = parser.parse_args()
    
    # Example travel request
    travel_request = """
    I'm planning a trip to Paris for 5 days in September. I'll be traveling from New York.
    I'm interested in art museums, historical sites, and trying local cuisine.
    My budget is around $2,000 for the entire trip, not including flights.
    Please help me create a detailed travel plan including flights, accommodation, 
    daily itinerary, budget breakdown, and any recommendations for my interests.
    """
    
    await run_travel_planner(args.pattern, travel_request)

if __name__ == "__main__":
    asyncio.run(main())