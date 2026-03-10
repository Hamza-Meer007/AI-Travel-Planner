import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import (
    LLM_QUOTA_ERROR_MESSAGE,
    LLM_RATE_LIMIT_ERROR_MESSAGE,
    LLM_AUTH_ERROR_MESSAGE,
    logger,
)
from backend.models import AIResponse, FlightRequest, HotelRequest, ItineraryRequest
from backend.search import search_flights, search_hotels, format_travel_data
from backend.ai_agents import get_ai_recommendation, generate_itinerary
from backend.llm import is_ai_service_error

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Travel Planning API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/search_flights/", response_model=AIResponse)
async def get_flight_recommendations(flight_request: FlightRequest):
    """Search flights and return results with an AI recommendation."""
    try:
        flights = await search_flights(flight_request)

        if isinstance(flights, dict) and "error" in flights:
            raise HTTPException(status_code=400, detail=flights["error"])

        if not flights:
            raise HTTPException(status_code=404, detail="No flights found")

        flights_text = format_travel_data("flights", flights)
        ai_recommendation = await get_ai_recommendation("flights", flights_text)

        return AIResponse(flights=flights, ai_flight_recommendation=ai_recommendation)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Flight search endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Flight search error: {str(e)}")


@app.post("/search_hotels/", response_model=AIResponse)
async def get_hotel_recommendations(hotel_request: HotelRequest):
    """Search hotels and return results with an AI recommendation."""
    try:
        hotels = await search_hotels(hotel_request)

        if isinstance(hotels, dict) and "error" in hotels:
            raise HTTPException(status_code=400, detail=hotels["error"])

        if not hotels:
            raise HTTPException(status_code=404, detail="No hotels found")

        hotels_text = format_travel_data("hotels", hotels)
        ai_recommendation = await get_ai_recommendation("hotels", hotels_text)

        return AIResponse(hotels=hotels, ai_hotel_recommendation=ai_recommendation)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Hotel search endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hotel search error: {str(e)}")


@app.post("/complete_search/", response_model=AIResponse)
async def complete_travel_search(
    flight_request: FlightRequest,
    hotel_request: Optional[HotelRequest] = None,
):
    """Search flights and hotels concurrently and return AI recommendations plus an itinerary."""
    try:
        if hotel_request is None:
            hotel_request = HotelRequest(
                location=flight_request.destination,
                check_in_date=flight_request.outbound_date,
                check_out_date=flight_request.return_date,
            )

        flight_task = asyncio.create_task(get_flight_recommendations(flight_request))
        hotel_task = asyncio.create_task(get_hotel_recommendations(hotel_request))

        flight_results, hotel_results = await asyncio.gather(
            flight_task, hotel_task, return_exceptions=True
        )

        if isinstance(flight_results, Exception):
            logger.error(f"Flight search failed: {str(flight_results)}")
            flight_results = AIResponse(
                flights=[], ai_flight_recommendation="Could not retrieve flights."
            )

        if isinstance(hotel_results, Exception):
            logger.error(f"Hotel search failed: {str(hotel_results)}")
            hotel_results = AIResponse(
                hotels=[], ai_hotel_recommendation="Could not retrieve hotels."
            )

        flights_text = format_travel_data("flights", flight_results.flights)
        hotels_text = format_travel_data("hotels", hotel_results.hotels)

        itinerary = ""
        ai_service_error = is_ai_service_error(
            flight_results.ai_flight_recommendation
        ) or is_ai_service_error(hotel_results.ai_hotel_recommendation)

        if flight_results.flights and hotel_results.hotels and not ai_service_error:
            itinerary = await generate_itinerary(
                destination=flight_request.destination,
                flights_text=flights_text,
                hotels_text=hotels_text,
                check_in_date=flight_request.outbound_date,
                check_out_date=flight_request.return_date,
            )
        elif ai_service_error:
            active_errors = {
                flight_results.ai_flight_recommendation,
                hotel_results.ai_hotel_recommendation,
            }
            if LLM_QUOTA_ERROR_MESSAGE in active_errors:
                itinerary = LLM_QUOTA_ERROR_MESSAGE
            elif LLM_RATE_LIMIT_ERROR_MESSAGE in active_errors:
                itinerary = LLM_RATE_LIMIT_ERROR_MESSAGE
            else:
                itinerary = LLM_AUTH_ERROR_MESSAGE

        return AIResponse(
            flights=flight_results.flights,
            hotels=hotel_results.hotels,
            ai_flight_recommendation=flight_results.ai_flight_recommendation,
            ai_hotel_recommendation=hotel_results.ai_hotel_recommendation,
            itinerary=itinerary,
        )

    except Exception as e:
        logger.exception(f"Complete travel search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Travel search error: {str(e)}")


@app.post("/generate_itinerary/", response_model=AIResponse)
async def get_itinerary(itinerary_request: ItineraryRequest):
    """Generate a travel itinerary from provided flight and hotel information."""
    try:
        itinerary = await generate_itinerary(
            destination=itinerary_request.destination,
            flights_text=itinerary_request.flights,
            hotels_text=itinerary_request.hotels,
            check_in_date=itinerary_request.check_in_date,
            check_out_date=itinerary_request.check_out_date,
        )
        return AIResponse(itinerary=itinerary)

    except Exception as e:
        logger.exception(f"Itinerary generation error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Itinerary generation error: {str(e)}"
        )
