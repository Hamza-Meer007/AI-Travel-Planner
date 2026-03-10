"""
TravelPlanner.py – entry point for the Travel AI Planner API.

All application logic lives inside the `backend/` package:
  backend/config.py    – environment variables, API keys, logger
  backend/models.py    – Pydantic request / response models
  backend/llm.py       – LLM initialisation and error helpers
  backend/search.py    – SerpAPI flight / hotel search + data formatters
  backend/ai_agents.py – CrewAI recommendation and itinerary agents
  backend/main.py      – FastAPI app and all route endpoints

Run with:  uvicorn TravelPlanner:app --reload
"""

import uvicorn

from backend.main import app  # noqa: F401 – re-exported for `uvicorn TravelPlanner:app`


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
