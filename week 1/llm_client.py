import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# load environment variables from .env 
load_dotenv()

# logger setup 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),   # logs saved to file
        logging.StreamHandler()           # logs also shown in terminal
    ]
)
logger = logging.getLogger(__name__)


class LLMClient:
   
    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview"):
        # API key loaded from environment 
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables!")
            raise EnvironmentError(
                "Missing GEMINI_API_KEY. Please set it in your .env file."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"LLMClient initialized with model: {model_name}")

    def call(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Send system + user prompt to Gemini and return parsed JSON response.

        Args:
            system_prompt: Instructions that define AI behavior
            user_prompt:   What the user actually asked

        Returns:
            Parsed JSON dict from AI response
        """

        # Combine system + user prompt 
        full_prompt = f"{system_prompt}\n\nUser: {user_prompt}"

        logger.info(f"Sending request | User prompt: '{user_prompt}'")

        try:
            # API Call
            response = self.model.generate_content(full_prompt)
            raw_text = response.text
            logger.info("Response received from Gemini API")
            logger.debug(f"Raw response: {raw_text}")

            # Parse JSON output 
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
                clean_text = clean_text.strip()

            parsed = json.loads(clean_text)
            logger.info("JSON parsed successfully")
            return parsed

        # Error Handling 
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return {"error": "AI response was not valid JSON", "raw": raw_text}

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"error": str(e)}