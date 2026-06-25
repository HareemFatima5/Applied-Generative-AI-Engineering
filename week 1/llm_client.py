# libraries import
import os
import json
import logging
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

load_dotenv()

# logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# fetch weather function
def fetch_weather(city: str) -> dict:
    owm_key = os.getenv("OWM_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": owm_key, "units": "metric"}
    
    logger.info(f"LLM triggered weather API call for: {city}")
    
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        weather_data = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_celsius": round(data["main"]["temp"], 1),
            "temperature_fahrenheit": round(data["main"]["temp"] * 9/5 + 32, 1),
            "condition": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_speed_kmh": round(data["wind"]["speed"] * 3.6, 1),
        }
        
        logger.info(f"Weather data fetched successfully for {city}")
        return weather_data
        
    except requests.exceptions.HTTPError:
        if res.status_code == 404:
            return {"error": f"City '{city}' not found."}
        return {"error": "Weather API error."}
    except Exception as e:
        return {"error": str(e)}


# LLM Client
class LLMClient:

    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview"):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables!")
            raise EnvironmentError("Missing GEMINI_API_KEY. Please set it in your .env file.")

        genai.configure(api_key=api_key)

        weather_tool = Tool(function_declarations=[
            FunctionDeclaration(
                name="fetch_weather",
                description="Fetches real-time weather data for a given city. Use this when the user asks about weather.",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city to fetch weather for. Extract this from the user's question."
                        }
                    },
                    "required": ["city"]
                }
            )
        ])

        self.model = genai.GenerativeModel(model_name, tools=[weather_tool])
        logger.info(f"LLMClient initialized with model: {model_name}")

    def call(self, system_prompt: str, user_prompt: str) -> dict:
        full_prompt = f"{system_prompt}\n\nUser Query: {user_prompt}"
        logger.info(f"Sending request to LLM | Query: '{user_prompt}'")

        try:
            chat = self.model.start_chat()
            
            # First response 
            response = chat.send_message(full_prompt)
            
            # track if we've handled function calls
            function_calls_handled = False
            
            # process any function calls the LLM wants to make
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call.name == "fetch_weather":
                    function_calls_handled = True
                    
                    # extract arguments from LLM's call
                    args = dict(part.function_call.args)
                    city = args.get("city")
                    
                    logger.info(f"LLM decided to call fetch_weather with city: {city}")
                    
                    # execute the API call
                    tool_result = fetch_weather(city)
                    
                    logger.info(f"Tool result: {json.dumps(tool_result, indent=2)}")
                    
                    # send the result back to the LLM for final response
                    response = chat.send_message(
                        {
                            "function_response": {
                                "name": "fetch_weather",
                                "response": tool_result
                            }
                        }
                    )
                    
                    logger.info("LLM received tool result and is generating final response")
                    break

            # get the final text response from LLM
            raw_text = response.text
            logger.info("Response received from Gemini API")

            # clean up the response
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
                clean_text = clean_text.strip()

            # parse JSON response
            parsed = json.loads(clean_text)
            
            # log that the LLM successfully orchestrated everything
            if function_calls_handled:
                logger.info("LLM successfully orchestrated the weather API call")
            else:
                logger.warning("LLM didn't call the weather tool - it may have used cached data")
                
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.error(f"Raw response: {raw_text}")
            return {"error": "AI response was not valid JSON", "raw": raw_text}

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"error": str(e)}