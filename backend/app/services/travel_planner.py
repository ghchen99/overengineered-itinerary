"""
Main travel planning service with streaming functionality
"""
import json
from datetime import datetime
from typing import AsyncGenerator

from ..models.request import StreamMessage
from ..models.travel import TravelRequest
from .ai_client import create_model_client
from .agents import create_sequential_travel_team
from ..utils.content_processing import extract_markdown_content
from ..utils.prompt_generation import generate_travel_prompt

async def stream_travel_plan(travel_request: TravelRequest) -> AsyncGenerator[str, None]:
    """Stream travel plan generation with real-time updates."""
    
    model_client = None
    
    try:
        # Initial setup message
        yield json.dumps(StreamMessage(
            type="progress",
            content=f"🚀 Starting travel plan generation for {travel_request.destination_city}, {travel_request.destination_country}",
            timestamp=datetime.now().isoformat()
        ).model_dump()) + "\n"
        
        # Generate travel prompt
        travel_prompt = generate_travel_prompt(travel_request)
        
        yield json.dumps(StreamMessage(
            type="progress",
            content="📝 Generated travel prompt and initializing AI agents...",
            timestamp=datetime.now().isoformat()
        ).model_dump()) + "\n"
        
        # Create model client and team
        model_client = create_model_client()
        team = create_sequential_travel_team(model_client, travel_request)
        
        yield json.dumps(StreamMessage(
            type="progress",
            content="🤖 AI agents ready - starting collaboration...",
            timestamp=datetime.now().isoformat()
        ).model_dump()) + "\n"
        
        # Track the latest markdown content
        latest_markdown = ""
        
        # Run the team and stream updates
        stream = team.run_stream(task=travel_prompt)
        
        async for message in stream:
            if hasattr(message, 'content') and hasattr(message, 'source') and message.source:
                agent_name = message.source
                
                # Send progress update
                yield json.dumps(StreamMessage(
                    type="progress",
                    agent=agent_name,
                    content=f"🔄 {agent_name} is working...",
                    timestamp=datetime.now().isoformat()
                ).model_dump()) + "\n"
                
                # Extract and check for markdown content
                clean_content = extract_markdown_content(message.content)
                
                # Only send markdown updates if content is substantial and markdown-formatted
                if len(clean_content) > 100 and clean_content.startswith('#'):
                    latest_markdown = clean_content
                    
                    # Determine if this is the final document
                    is_final = agent_name == "CriticAgent" and "DOCUMENT_READY" in message.content
                    
                    yield json.dumps(StreamMessage(
                        type="final" if is_final else "markdown_update",
                        agent=agent_name,
                        content=clean_content,
                        timestamp=datetime.now().isoformat(),
                        character_count=len(clean_content)
                    ).model_dump()) + "\n"
                    
                    if is_final:
                        yield json.dumps(StreamMessage(
                            type="progress",
                            content="✅ Travel plan complete!",
                            timestamp=datetime.now().isoformat()
                        ).model_dump()) + "\n"
                        break
        
        # If we didn't get a final document, send the latest as final
        if latest_markdown and not latest_markdown.startswith("✅"):
            yield json.dumps(StreamMessage(
                type="final",
                content=latest_markdown,
                timestamp=datetime.now().isoformat(),
                character_count=len(latest_markdown)
            ).model_dump()) + "\n"
            
    except Exception as e:
        yield json.dumps(StreamMessage(
            type="error",
            content=f"❌ Error generating travel plan: {str(e)}",
            timestamp=datetime.now().isoformat()
        ).model_dump()) + "\n"
        
    finally:
        if model_client:
            try:
                await model_client.close()
            except:
                pass