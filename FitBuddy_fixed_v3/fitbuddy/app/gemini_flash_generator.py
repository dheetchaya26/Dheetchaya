"""
Fast nutrition/recovery tip generation using the current Google GenAI SDK.
"""

import os
import logging

from google import genai
from google.genai import types

logger = logging.getLogger("fitbuddy.gemini_flash_generator")

GEMINI_TIP_MODEL = "gemini-3.8-flash"
API_TIMEOUT_MS = 20000

_FALLBACK_TIP = (
    "Stay hydrated and include a suitable source of protein and balanced foods "
    "to support recovery and progress toward your fitness goal."
)


def _get_client():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found; fallback nutrition tip will be used.")
        return None

    try:
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=API_TIMEOUT_MS),
        )
    except Exception:
        logger.exception("Failed to initialize Gemini client.")
        return None


def generate_nutrition_tip_with_flash(goal: str) -> str:
    client = _get_client()
    if client is None:
        return _FALLBACK_TIP

    prompt = f"""
Give one short, practical nutrition or recovery tip for a person whose fitness
goal is: {goal}. Keep it to 2-3 sentences, plain text, and avoid markdown.
"""

    try:
        logger.info("Calling Gemini for nutrition tip...")
        response = client.models.generate_content(
            model=GEMINI_TIP_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=180,
                temperature=0.4,
            ),
        )
        text = (response.text or "").strip()
        logger.info("Nutrition tip generation completed.")
        return text if text else _FALLBACK_TIP
    except Exception:
        logger.exception("Gemini nutrition tip generation failed; using fallback.")
        return _FALLBACK_TIP
