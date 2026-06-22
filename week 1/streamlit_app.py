# importing libraries
import os
import logging
import streamlit as st
from llm_client import LLMClient
import requests

# logger to save error messages
logger = logging.getLogger(__name__)

# system prompt
SYSTEM_PROMPT = """You are a weather assistant.
 
You will receive real weather data for a city. Based on this data,
respond ONLY with a valid JSON object in exactly this format - no extra text:
 
{
  "city": "<city name>",
  "country": "<country name>",
  "temperature_celsius": "<value>",
  "temperature_fahrenheit": "<value>",
  "condition": "<weather condition>",
  "humidity": "<value>",
  "wind_speed_kmh": "<value>",
  "advice": "<one short practical tip based on the actual weather>"
}
"""

# fetch weather function
def fetch_weather(city:str, owm_key:str) -> dict:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": owm_key, "units": "metric"}
        
        # error handling
        try:
            res = requests.get(url,params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_celsius": round(data["main"]["temp"], 1),
            "temperature_fahrenheit": round(data["main"]["temp"] * 9/5 + 32, 1),
            "condition": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_speed_kmh": round(data["wind"]["speed"] * 3.6, 1),
        }
        
        except requests.exceptions.HTTPError:
            if res.status_code == 404:
                return {"error": f"City '{city}' not found."}
            return {"error": "Weather API error."}
        
        
        # catches any other error i.e network problems
        except Exception as e:
                return {"error": str(e)}
 
# streamlit app           
st.set_page_config(page_title="Weather App", layout="centered")
st.title("AI Weather App")
st.divider()
 
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("Gemini API Key", type="password")
    owm_key = st.text_input("OpenWeatherMap API Key", type="password")
 
if gemini_key:
    os.environ["GEMINI_API_KEY"] = gemini_key
 
city = st.text_input("City Name", placeholder="e.g. Lahore, Tokyo, London")
get_weather = st.button("Get Weather", type="primary", use_container_width=True)
 
if get_weather:
    if not city.strip():
        st.warning("Please enter a city name.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("Gemini API key missing.")
    elif not owm_key:
        st.error("OpenWeatherMap API key missing.")
    else:
        with st.spinner(f"Fetching weather for {city}..."):
            weather_data = fetch_weather(city, owm_key)
 
            if "error" in weather_data:
                st.error(weather_data["error"])
            else:
                try:
                    client = LLMClient()
                    result = client.call(
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=f"Here is the real weather data for {city}: {weather_data}"
                    )
 
                    if "error" in result:
                        st.error(f"Gemini error: {result['error']}")
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
 
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(e)