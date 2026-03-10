import asyncio

from fastapi import HTTPException
from serpapi import GoogleSearch

from backend.config import SERP_API_KEY, logger
from backend.models import FlightInfo, FlightRequest, HotelInfo, HotelRequest


# ---------------------------------------------------------------------------
# Generic SerpAPI runner
# ---------------------------------------------------------------------------

async def run_search(params: dict) -> dict:
    """Run a SerpAPI search asynchronously and return the raw result dict."""
    try:
        return await asyncio.to_thread(lambda: GoogleSearch(params).get_dict())
    except Exception as e:
        logger.exception(f"SerpAPI search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search API error: {str(e)}")


# ---------------------------------------------------------------------------
# Flight search
# ---------------------------------------------------------------------------

async def search_flights(flight_request: FlightRequest):
    """Fetch real-time flight options from Google via SerpAPI."""
    logger.info(
        f"Searching flights: {flight_request.origin} → {flight_request.destination}"
    )

    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": flight_request.origin.strip().upper(),
        "arrival_id": flight_request.destination.strip().upper(),
        "outbound_date": flight_request.outbound_date,
        "return_date": flight_request.return_date,
        "currency": "USD",
    }

    search_results = await run_search(params)

    if "error" in search_results:
        logger.error(f"Flight search error: {search_results['error']}")
        return {"error": search_results["error"]}

    best_flights = search_results.get("best_flights", [])
    if not best_flights:
        logger.warning("No flights found in search results")
        return []

    formatted_flights = []
    for flight in best_flights:
        if not flight.get("flights"):
            continue

        first_leg = flight["flights"][0]
        dep_airport = first_leg.get("departure_airport", {})
        arr_airport = first_leg.get("arrival_airport", {})

        formatted_flights.append(
            FlightInfo(
                airline=first_leg.get("airline", "Unknown Airline"),
                price=str(flight.get("price", "N/A")),
                duration=f"{flight.get('total_duration', 'N/A')} min",
                stops=(
                    "Nonstop"
                    if len(flight["flights"]) == 1
                    else f"{len(flight['flights']) - 1} stop(s)"
                ),
                departure=(
                    f"{dep_airport.get('name', 'Unknown')} "
                    f"({dep_airport.get('id', '???')}) "
                    f"at {dep_airport.get('time', 'N/A')}"
                ),
                arrival=(
                    f"{arr_airport.get('name', 'Unknown')} "
                    f"({arr_airport.get('id', '???')}) "
                    f"at {arr_airport.get('time', 'N/A')}"
                ),
                travel_class=first_leg.get("travel_class", "Economy"),
                return_date=flight_request.return_date,
                airline_logo=first_leg.get("airline_logo", ""),
            )
        )

    logger.info(f"Found {len(formatted_flights)} flights")
    return formatted_flights


# ---------------------------------------------------------------------------
# Hotel search
# ---------------------------------------------------------------------------

async def search_hotels(hotel_request: HotelRequest):
    """Fetch hotel options from Google via SerpAPI."""
    logger.info(f"Searching hotels for: {hotel_request.location}")

    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_hotels",
        "q": hotel_request.location,
        "hl": "en",
        "gl": "us",
        "check_in_date": hotel_request.check_in_date,
        "check_out_date": hotel_request.check_out_date,
        "currency": "USD",
        "sort_by": 3,
        "rating": 8,
    }

    search_results = await run_search(params)

    if "error" in search_results:
        logger.error(f"Hotel search error: {search_results['error']}")
        return {"error": search_results["error"]}

    hotel_properties = search_results.get("properties", [])
    if not hotel_properties:
        logger.warning("No hotels found in search results")
        return []

    formatted_hotels = []
    for hotel in hotel_properties:
        try:
            # SerpAPI returns neighbourhood/address, not a flat "location" key
            location = (
                hotel.get("neighborhood")
                or hotel.get("address")
                or "N/A"
            )
            formatted_hotels.append(
                HotelInfo(
                    name=hotel.get("name", "Unknown Hotel"),
                    price=hotel.get("rate_per_night", {}).get("lowest", "N/A"),
                    rating=float(hotel.get("overall_rating") or 0.0),
                    location=location,
                    link=hotel.get("link", ""),
                )
            )
        except Exception as e:
            logger.warning(f"Error formatting hotel data: {str(e)}")

    logger.info(f"Found {len(formatted_hotels)} hotels")
    return formatted_hotels


# ---------------------------------------------------------------------------
# Data formatters
# ---------------------------------------------------------------------------

def format_travel_data(data_type: str, data: list) -> str:
    """Format flight or hotel data into a human-readable string for AI prompts."""
    if not data:
        return f"No {data_type} available."

    if data_type == "flights":
        formatted_text = "**Available flight options (prices in USD)**:\n\n"
        for i, flight in enumerate(data):
            formatted_text += (
                f"**Flight {i + 1}:**\n"
                f"✈️ **Airline:** {flight.airline}\n"
                f"💵 **Price (USD):** ${flight.price}\n"
                f"⏱️ **Duration:** {flight.duration}\n"
                f"🛑 **Stops:** {flight.stops}\n"
                f"🕔 **Departure:** {flight.departure}\n"
                f"🕖 **Arrival:** {flight.arrival}\n"
                f"💺 **Class:** {flight.travel_class}\n\n"
            )

    elif data_type == "hotels":
        formatted_text = "**Available Hotel Options (prices in USD)**:\n\n"
        for i, hotel in enumerate(data):
            formatted_text += (
                f"**Hotel {i + 1}:**\n"
                f"🏨 **Name:** {hotel.name}\n"
                f"💵 **Price (USD):** {hotel.price}\n"
                f"⭐ **Rating:** {hotel.rating}/5\n"
                f"📍 **Location:** {hotel.location}\n"
                f"🔗 **More Info:** [Link]({hotel.link})\n\n"
            )

    else:
        return "Invalid data type."

    return formatted_text.strip()
