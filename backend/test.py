#!/usr/bin/env python3
"""
Test script for the Travel Planner FastAPI streaming endpoint.
This script demonstrates how to consume the streaming travel plan generation API.
Updated to print full markdown content instead of previews.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

def test_travel_api(base_url: str = "http://localhost:8000"):
    """
    Test the travel planning API with streaming responses.
    
    Args:
        base_url: The base URL of the FastAPI server
    """
    
    # Test data - modify as needed
    travel_request = {
        "destination_city": "Tokyo",
        "destination_country": "Japan",
        "depart_date": "2025-10-10",
        "return_date": "2025-10-17",
        "priority": "food",
        "budget_level": "flexible",
        "departure_airport": "LHR",
        "destination_airport": None,
        "additional_preferences": "interested in temples and authentic experiences"
    }
    
    print("=" * 80)
    print("🧪 TESTING TRAVEL PLANNER API")
    print("=" * 80)
    print(f"📡 API URL: {base_url}")
    print(f"🎯 Destination: {travel_request['destination_city']}, {travel_request['destination_country']}")
    print(f"📅 Dates: {travel_request['depart_date']} to {travel_request['return_date']}")
    print(f"🎨 Priority: {travel_request['priority']}")
    print(f"💰 Budget: {travel_request['budget_level']}")
    print("-" * 80)
    
    # First, test health endpoint
    try:
        print("🏥 Testing health endpoint...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {health_response.json()}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure the FastAPI server is running:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000")
        return
    
    print("\n" + "=" * 80)
    print("🚀 STARTING STREAMING TRAVEL PLAN GENERATION")
    print("=" * 80)
    
    # Variables to track progress
    start_time = time.time()
    message_count = 0
    latest_markdown = ""
    agents_seen = set()
    
    try:
        # Make streaming request
        response = requests.post(
            f"{base_url}/generate-travel-plan",
            json=travel_request,
            stream=True,
            timeout=300,  # 5 minute timeout
            headers={"Accept": "application/x-ndjson"}
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        print("📡 Connected to streaming endpoint...")
        print("⏳ Waiting for agent responses...\n")
        
        # Process streaming response line by line
        for line in response.iter_lines(decode_unicode=True):
            if not line.strip():
                continue
                
            try:
                # Parse JSON message
                message = json.loads(line)
                message_count += 1
                
                # Extract message details
                msg_type = message.get("type", "unknown")
                agent = message.get("agent")
                content = message.get("content", "")
                timestamp = message.get("timestamp", "")
                char_count = message.get("character_count")
                
                # Track agents we've seen
                if agent:
                    agents_seen.add(agent)
                
                # Format timestamp for display
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
                
                # Handle different message types
                if msg_type == "progress":
                    agent_str = f" [{agent}]" if agent else ""
                    print(f"[{time_str}] 📋{agent_str} {content}")
                    
                elif msg_type == "markdown_update":
                    latest_markdown = content
                    print(f"[{time_str}] 📝 [{agent}] Updated travel plan ({char_count:,} chars)")
                    print("-" * 80)
                    print("📄 FULL MARKDOWN CONTENT:")
                    print("-" * 80)
                    print(content)
                    print("-" * 80)
                    print("END OF MARKDOWN UPDATE")
                    print("-" * 80)
                    print()
                    
                elif msg_type == "final":
                    latest_markdown = content
                    print(f"[{time_str}] 🎉 [{agent or 'System'}] FINAL DOCUMENT READY!")
                    print(f"        📄 Total length: {char_count:,} characters")
                    print("=" * 80)
                    print("🎯 FINAL COMPLETE TRAVEL PLAN:")
                    print("=" * 80)
                    print(content)
                    print("=" * 80)
                    print("END OF FINAL TRAVEL PLAN")
                    print("=" * 80)
                    break
                    
                elif msg_type == "error":
                    print(f"[{time_str}] ❌ ERROR: {content}")
                    return
                    
                else:
                    print(f"[{time_str}] ❓ Unknown message type: {msg_type}")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON: {e}")
                print(f"   Raw line: {line[:100]}...")
                continue
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 GENERATION COMPLETE - SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
        print(f"📨 Messages received: {message_count}")
        print(f"🤖 Agents involved: {', '.join(sorted(agents_seen))}")
        print(f"📄 Final document length: {len(latest_markdown):,} characters")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - the API might be taking too long to respond")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")

def test_multiple_destinations():
    """Test multiple destinations to verify API reliability."""
    
    destinations = [
        {"city": "Paris", "country": "France", "priority": "culture"},
        {"city": "Bangkok", "country": "Thailand", "priority": "food"},
        {"city": "Rome", "country": "Italy", "priority": "history"},
    ]
    
    print("🧪 TESTING MULTIPLE DESTINATIONS")
    print("=" * 80)
    
    for i, dest in enumerate(destinations, 1):
        print(f"\n🌍 Test {i}/{len(destinations)}: {dest['city']}, {dest['country']}")
        print("-" * 40)
        
        # Quick test request (abbreviated for testing)
        travel_request = {
            "destination_city": dest["city"],
            "destination_country": dest["country"],
            "depart_date": "2025-08-15",
            "return_date": "2025-08-20",
            "priority": dest["priority"],
            "budget_level": "moderate",
            "departure_airport": "JFK"
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/generate-travel-plan",
                json=travel_request,
                stream=True,
                timeout=120  # Increased timeout since we're showing full content
            )
            
            if response.status_code == 200:
                message_count = 0
                for line in response.iter_lines(decode_unicode=True):
                    if line.strip():
                        try:
                            message = json.loads(line)
                            message_count += 1
                            
                            msg_type = message.get("type", "unknown")
                            content = message.get("content", "")
                            
                            # For multiple destination testing, show progress but limit full markdown output
                            if msg_type == "progress":
                                print(f"   📋 {content}")
                            elif msg_type == "markdown_update":
                                print(f"   📝 Markdown updated ({len(content):,} chars)")
                            elif msg_type == "final":
                                print(f"   🎉 Final plan ready ({len(content):,} chars)")
                                print("-" * 60)
                                print("FINAL PLAN:")
                                print(content)
                                print("-" * 60)
                                break
                                
                        except json.JSONDecodeError:
                            continue
                            
                print(f"   ✅ Completed ({message_count} messages)")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Delay between tests
        print(f"   ⏳ Waiting before next test...")
        time.sleep(3)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Travel Planner API")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API (default: http://localhost:8000)")
    parser.add_argument("--multiple", action="store_true",
                       help="Test multiple destinations quickly")
    
    args = parser.parse_args()
    
    if args.multiple:
        test_multiple_destinations()
    else:
        test_travel_api(args.url)
    
    print("\n✅ Test completed!")