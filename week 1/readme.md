# AI Weather App

A Streamlit app where the LLM (Google Gemini) intelligently orchestrates weather API calls and displays real-time weather data with helpful advice.

## Features
- **LLM-Driven Architecture** - Gemini AI decides when and how to call the weather API
- **Intelligent Tool Calling** - LLM extracts city names and triggers OpenWeatherMap API
- **Real-Time Weather Data** - Fetches live weather from OpenWeatherMap API
- **AI-Powered Formatting** - Gemini formats weather data with practical advice
- **Clean, Responsive UI** - Professional metrics display with Streamlit
- **Comprehensive Logging** - Track LLM decisions and API calls
- **Error Handling** - Graceful error management for API failures

## How It Works
1. User enters a city name
2. LLM receives the query and **decides to call** the weather API
3. LLM **provides the city parameter** to the `fetch_weather` tool
4. Tool executes the actual OpenWeatherMap API call
5. Weather data returns to the LLM
6. LLM formats the response in JSON with helpful advice
7. User sees beautifully displayed weather metrics

## Tech Stack
- **Streamlit** - UI framework
- **Google Gemini AI** - LLM that orchestrates API calls & generates responses
- **OpenWeatherMap API** - Real weather data source
- **Python** - Backend logic

## How to Use
- Enter both API keys in the sidebar 
- Type a city name
- Click "Get Weather"

## Deployment

![Deployment](assets/pic.PNG)