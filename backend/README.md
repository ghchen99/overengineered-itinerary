# Travel Planner API

A FastAPI-based travel planning service that uses AI agents to generate comprehensive travel plans with streaming responses.

## Project Structure

```
backend/
├── main.py                      # Entry point - run this file
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── app/                        # Main application package
    ├── __init__.py
    ├── api.py                  # FastAPI app factory and routes
    ├── models/                 # Data models
    │   ├── __init__.py
    │   ├── request.py          # Pydantic API models
    │   └── travel.py           # Internal data classes
    ├── services/               # Business logic
    │   ├── __init__.py
    │   ├── ai_client.py        # Azure OpenAI client setup
    │   ├── agents.py           # AI agent definitions
    │   └── travel_planner.py   # Main travel planning service
    └── utils/                  # Helper functions
        ├── __init__.py
        ├── content_processing.py   # Text/markdown processing
        └── prompt_generation.py    # AI prompt generation
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export AZURE_OPENAI_MODEL_NAME="your-model-name"
export AZURE_DEPLOYMENT_NAME="your-deployment-name"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_VERSION="your-api-version"
export AZURE_OPENAI_API_KEY="your-api-key"
```

## Running the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /generate-travel-plan` - Generate a travel plan with streaming responses
- `GET /health` - Health check endpoint
- `GET /` - API information

## Architecture

The application follows a clean architecture pattern:

- **API Layer** (`api.py`): FastAPI routes and middleware configuration
- **Service Layer** (`services/`): Business logic and AI agent orchestration
- **Models** (`models/`): Data structures for API and internal use
- **Utils** (`utils/`): Helper functions for content processing and prompt generation

## AI Agents

The system uses 5 specialized AI agents working in sequence:

1. **ItineraryAgent**: Creates the initial travel plan structure
2. **ImagesAgent**: Adds Google Images links to locations
3. **FlightsAgent**: Adds flight booking information
4. **AccommodationAgent**: Adds accommodation booking links
5. **CriticAgent**: Final review and quality control

## Features

- Streaming responses for real-time updates
- Modular AI agent architecture
- Clean separation of concerns
- CORS enabled for frontend integration
- Comprehensive error handling
