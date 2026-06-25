import os
import logging
import streamlit as st
from llm_client import LLMClient

logger = logging.getLogger(__name__)

# System prompt 
SYSTEM_PROMPT = """You are a weather assistant that uses the fetch_weather tool to get real-time data.

Instructions:
1. When user asks about weather, call the fetch_weather tool
2. Do not use cached or imagined weather data
3. After receiving the tool result, respond ONLY with a valid JSON object in exactly this format:

{
  "city": "<city from tool result>",
  "country": "<country from tool result>",
  "temperature_celsius": "<value from tool result>",
  "temperature_fahrenheit": "<value from tool result>",
  "condition": "<condition from tool result>",
  "humidity": "<humidity from tool result>",
  "wind_speed_kmh": "<wind speed from tool result>",
  "advice": "<one short practical tip based on the actual weather>"
}

If the tool returns an error, respond with:
{
  "error": "<error message from tool>"
}

Always call the fetch_weather tool for every weather query."""

# Streamlit app
st.set_page_config(page_title="Weather App", layout="centered")
st.title("AI Weather App")
st.divider()

with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("Gemini API Key", type="password")
    owm_key = st.text_input("OpenWeatherMap API Key", type="password")

if gemini_key:
    os.environ["GEMINI_API_KEY"] = gemini_key
if owm_key:
    os.environ["OWM_API_KEY"] = owm_key

city = st.text_input("City Name", placeholder="e.g. Lahore, Tokyo, London")
get_weather = st.button("Get Weather", type="primary", use_container_width=True)

if get_weather:
    if not city.strip():
        st.warning("Please enter a city name.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("Gemini API key missing.")
    elif not os.getenv("OWM_API_KEY"):
        st.error("OpenWeatherMap API key missing.")
    else:
        with st.spinner(f"Fetching weather for {city}..."):
            try:
                client = LLMClient()
                result = client.call(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=f"What is the current weather in {city}? Use the fetch_weather tool to get the data."
                )

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader(f"{result.get('city')}, {result.get('country')}")
                    st.caption(result.get('condition'))

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Temperature (C)", f"{result.get('temperature_celsius')} C")
                        st.metric("Temperature (F)", f"{result.get('temperature_fahrenheit')} F")
                    with col2:
                        st.metric("Humidity", f"{result.get('humidity')} %")
                    with col3:
                        st.metric("Wind Speed", f"{result.get('wind_speed_kmh')} km/h")

                    st.info(result.get('advice'))

                    with st.expander("Raw JSON"):
                        st.json(result)
                    
                    st.success("LLM successfully called the weather API")

            except Exception as e:
                st.error(f"Error: {e}")
                logger.error(e)