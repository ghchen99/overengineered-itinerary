"""
FastAPI application factory and configuration
"""
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .models.request import TravelPlanRequest
from .models.travel import TravelRequest
from .services.travel_planner import stream_travel_plan

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(title="Travel Planner API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js dev server
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # Alternative port
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    @app.post("/generate-travel-plan")
    async def generate_travel_plan(request: TravelPlanRequest):
        """Generate a travel plan with streaming updates."""
        
        try:
            # Convert Pydantic model to internal dataclass
            travel_request = TravelRequest(
                destination_city=request.destination_city,
                destination_country=request.destination_country,
                depart_date=request.depart_date,
                return_date=request.return_date,
                priority=request.priority,
                budget_level=request.budget_level,
                departure_airport=request.departure_airport,
                destination_airport=request.destination_airport,
                additional_preferences=request.additional_preferences
            )
            
            return StreamingResponse(
                stream_travel_plan(travel_request),
                media_type="application/x-ndjson",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Travel Planner API",
            "version": "1.0.0",
            "endpoints": {
                "generate_plan": "/generate-travel-plan (POST)",
                "health": "/health (GET)"
            }
        }
    
    return app