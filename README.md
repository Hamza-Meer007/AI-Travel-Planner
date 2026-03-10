# ✈️ AI-Powered Travel Planner

An end-to-end **AI-powered travel planning system** that allows users to search for flights, find hotels, and generate **personalized travel itineraries** using **Agentic AI**.

This project demonstrates how to build a **real-world GenAI application** using **FastAPI**, **Streamlit**, **CrewAI**, and **Large Language Models (LLMs)**, integrated with **real-time travel data from SerpAPI**.

---

## 🚀 Features

- 🔍 **Real-time flight search** using Google Flights (via SerpAPI)
- 🏨 **Real-time hotel search** using Google Hotels (via SerpAPI)
- 🤖 **AI-powered recommendations** for best flights and hotels
- 🧠 **Agentic AI architecture** using CrewAI
- 📅 **AI-generated day-by-day travel itinerary**
- ⚡ **Async FastAPI backend** for performance
- 🖥️ **Interactive Streamlit frontend**
- 📥 **Downloadable itinerary (Markdown)**

---

## 🏗️ System Architecture

**Flow Overview:**

1. User enters travel details via Streamlit UI
2. Streamlit sends requests to FastAPI backend
3. FastAPI fetches real-time data from SerpAPI
4. CrewAI agents analyze flight & hotel options
5. AI recommends best options
6. LLM generates a complete travel itinerary
7. Results are returned and displayed in the UI

---

## 🧠 Agentic AI Design

This system uses **multiple AI agents**, each with a specific role:

- ✈️ **Flight Analyst Agent**
  - Evaluates price, duration, stops, and comfort
- 🏨 **Hotel Analyst Agent**
  - Analyzes price, rating, location, and amenities
- 📅 **Travel Planner Agent**
  - Generates a structured day-by-day itinerary

Agents collaborate using **CrewAI** and are powered by **LLMs**.

---

## 🛠️ Tech Stack

### Backend

- **FastAPI**
- **Python (Async / asyncio)**
- **Pydantic**
- **CrewAI**
- **OpenAI / LLMs**
- **SerpAPI**

### Frontend

- **Streamlit**

### Other Tools

- **dotenv** (Environment variables)
- **Uvicorn** (ASGI server)
- **Logging**

---

## 📂 Project Structure

```text
.
├── Travel-ai-planner/
│   ├── TravelPlanner.py
│   ├── TravelPlanner_Streamlit.py
│
├── .env                     # API keys
├── requirements.txt
└── README.md

🔑 Environment Variables

Create a .env file in the backend directory:

OPENAI_API_KEY=your_openai_api_key
SERP_API_KEY=your_serpapi_key

▶️ How to Run the Project

1️⃣ Install Dependencies
pip install -r requirements.txt

2️⃣ Start FastAPI Backend
uvicorn TravelPlanner:app --reload

Backend will run at:
http://localhost:8000

3️⃣ Start Streamlit Frontend
streamlit run TravelPlanner_Streamlit.py
Frontend will open at:

http://localhost:8501

🔌 API Endpoints
Endpoint	Description
/search_flights/	    Search flights + AI recommendation
/search_hotels/	      Search hotels + AI recommendation
/complete_search/	    Flights + hotels + itinerary
/generate_itinerary/	Generate itinerary from inputs

📸 UI Preview
Flight cards with price, duration, and class
Hotel cards with rating and location
AI recommendation panels
Day-by-day itinerary with emojis
Download itinerary button

🎯 Use Cases

AI travel assistants
Agentic AI demos
GenAI portfolio projects
System design interviews
Startup MVPs

🧩 Future Improvements

✅ User authentication
💾 Caching & cost optimization
📊 LLM usage tracking
🌍 Multi-city travel support
🧠 Structured AI outputs (JSON)
📱 Mobile-friendly UI
```
