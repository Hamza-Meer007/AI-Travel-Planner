import asyncio
from datetime import datetime

from openai import AuthenticationError, RateLimitError
from crewai import Agent, Task, Crew, Process

from backend.config import LLM_PROVIDER_DISPLAY_NAME, LLM_AUTH_ERROR_MESSAGE, logger
from backend.llm import initialize_llm, get_llm_rate_limit_message


# ---------------------------------------------------------------------------
# AI recommendation (flights & hotels)
# ---------------------------------------------------------------------------

async def get_ai_recommendation(data_type: str, formatted_data: str) -> str:
    """Get an AI-powered recommendation for flights or hotels using a CrewAI agent."""
    logger.info(f"Getting {data_type} analysis from AI")
    llm_model = initialize_llm()

    if data_type == "flights":
        role = "AI Flight Analyst"
        goal = "Recommend the best flight by assessing price, duration, stops, and convenience."
        backstory = "An AI specialist that performs detailed comparisons of flight options across multiple criteria."
        description = """
        Based on the information below, evaluate the available flights and recommend the optimal option.

        **Recommendation Summary:**
        - **💵 Price (USD):** Provide a thorough justification for why this flight is the most cost-effective and convenient choice. Always use USD ($) when referencing prices.
        - **⏱️ Duration:** Provide an analysis showing why this flight has a superior total travel time relative to alternatives.
        - **🛑 Stops:** Describe how this flight minimizes layovers while maintaining overall efficiency.
        - **💺 Travel Class:** Provide a detailed assessment of this flight's comfort features and amenities, highlighting why they outperform alternatives.

        Use the provided flight data as the basis for your recommendation. Justify your choice using clear reasoning for each attribute. Do not repeat the raw flight details in your response.
        """

    elif data_type == "hotels":
        role = "AI Hotel Analyst"
        goal = "Analyze hotel options and recommend the best one by considering price, rating, location, and amenities."
        backstory = "AI expert which provides in-depth analysis in comparing hotel options based on multiple factors."
        description = """
        Using the analysis below, recommend the best hotel with a detailed explanation considering price, rating, location, and amenities.

        **AI Hotel Recommendation**
        Based on the analysis below, we recommend the top hotel option:

        **Recommendation Summary:**
        - **💵 Price (USD):** This hotel represents the most cost-effective option, providing excellent amenities and services relative to its price. Always use USD ($) when referencing prices.
        - **⭐ Rating:** The hotel's higher rating reflects consistently positive reviews and a higher level of service quality.
        - **📍 Location:** Strategically located near major points of interest, the hotel offers excellent convenience for travelers.
        - **🏨 Amenities:** With offerings such as high-speed Wi-Fi, a pool, fitness facilities, and free breakfast, the hotel meets diverse traveler needs.

        📝 **Reasoning Requirements:**
        - Each section should provide a clear rationale demonstrating why this hotel is optimal.
        - Compare with other available options and highlight the standout factors.
        - Provide well-organized justification to make the recommendation transparent and easy to understand.
        """

    else:
        raise ValueError(f"Invalid data type for AI recommendation: {data_type!r}")

    agent = Agent(role=role, goal=goal, backstory=backstory, llm=llm_model, verbose=False)
    task = Task(
        description=f"{description}\n\nData to analyze:\n{formatted_data}",
        agent=agent,
        expected_output=(
            f"A concise, data-driven recommendation highlighting the top {data_type} "
            "selection according to the analyzed details."
        ),
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)

    try:
        crew_results = await asyncio.to_thread(crew.kickoff)
        if hasattr(crew_results, "outputs") and crew_results.outputs:
            return crew_results.outputs[0]
        elif hasattr(crew_results, "get"):
            return crew_results.get(role, f"No {data_type} recommendation available.")
        return str(crew_results)

    except AuthenticationError:
        logger.exception(
            f"Error in AI {data_type} analysis: invalid {LLM_PROVIDER_DISPLAY_NAME} credentials"
        )
        return LLM_AUTH_ERROR_MESSAGE
    except RateLimitError as error:
        logger.exception(
            f"Error in AI {data_type} analysis: {LLM_PROVIDER_DISPLAY_NAME} quota or rate limit issue"
        )
        from backend.llm import get_llm_rate_limit_message
        return get_llm_rate_limit_message(error)
    except Exception as e:
        logger.exception(f"Error in AI {data_type} analysis: {str(e)}")
        return f"Unable to generate {data_type} recommendation due to an error."


# ---------------------------------------------------------------------------
# Itinerary generation
# ---------------------------------------------------------------------------

async def generate_itinerary(
    destination: str,
    flights_text: str,
    hotels_text: str,
    check_in_date: str,
    check_out_date: str,
) -> str:
    """Generate a detailed day-by-day travel itinerary using a CrewAI agent."""
    try:
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        days = (check_out - check_in).days

        llm_model = initialize_llm()

        agent = Agent(
            role="AI Travel Planner",
            goal="Generate a full itinerary for the traveler, incorporating both flight schedules and hotel accommodations.",
            backstory="AI-driven itinerary planner offering an optimized daily plan including travel logistics, accommodation, and key experiences.",
            llm=llm_model,
            verbose=False,
        )

        task = Task(
            description=f"""
            Based on the following details, create a {days}-day itinerary for the user:

            **Flight Details**:
            {flights_text}

            **Hotel Details**:
            {hotels_text}

            **Destination**: {destination}

            **Travel Dates**: {check_in_date} to {check_out_date} ({days} days)

            The itinerary should include:
            - Flight Details ✈️
                Arrival and departure times, flight numbers and airlines, duration and layovers
            - Hotel Information 🏨
                Check-in and check-out times, hotel name, rating, location, key amenities
            - Day-by-Day Activities 📅
                Morning, afternoon, and evening plans with estimated durations
            - Must-Visit Attractions 🏛️
                Top landmarks, suggested visit times, tips for avoiding crowds
            - Restaurant Recommendations 🍴
                Breakfast, lunch, and dinner options, local favorites, approximate price range
            - Local Transportation Tips 🚌🚇
                Best modes of transport, estimated travel time, cost-saving options

            **Formatting Guidelines**:
            - Use # for the main title, ## for each day, ### for sub-sections
            - Use emojis: 🏛️ attractions, 🍽️ meals, 🏨 hotel, ✈️ flights
            - Use bullet points for activities, restaurants, and attractions
            - Include approximate start/end times (e.g., 09:00 AM – 11:00 AM)
            - Bold key names (hotel name, flight numbers, restaurant names)
            """,
            agent=agent,
            expected_output=(
                "A comprehensive, Markdown-formatted itinerary including flights, accommodations, "
                "and a detailed daily schedule, enhanced with emojis, headers, and bullet points."
            ),
        )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
        crew_results = await asyncio.to_thread(crew.kickoff)

        if hasattr(crew_results, "outputs") and crew_results.outputs:
            return crew_results.outputs[0]
        elif hasattr(crew_results, "get"):
            return crew_results.get("AI Travel Planner", "No itinerary available.")
        return str(crew_results)

    except AuthenticationError:
        logger.exception(
            f"Error generating itinerary: invalid {LLM_PROVIDER_DISPLAY_NAME} credentials"
        )
        return LLM_AUTH_ERROR_MESSAGE
    except RateLimitError as error:
        logger.exception(
            f"Error generating itinerary: {LLM_PROVIDER_DISPLAY_NAME} quota or rate limit issue"
        )
        return get_llm_rate_limit_message(error)
    except Exception as e:
        logger.exception(f"Error generating itinerary: {str(e)}")
        return "Unable to generate itinerary due to an error. Please try again later."
