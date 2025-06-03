"""
Main entry point for the Travel Planner API
"""
import uvicorn
from app.api import create_app

def main():
    """Run the FastAPI application"""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()