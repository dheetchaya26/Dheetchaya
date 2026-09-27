"""
Fast nutrition / recovery tip generation using Gemini Flash.
"""

import os
import logging

import google.generativeai as genai

logger = logging.getLogger("fitbuddy.gemini_flash_generator")

GEMINI_FLASH_MODEL = "gemini-1.5-flash"

_FALLBACK_TIP = (
    "Stay hydrated and include a good source of protein in every meal to "
    "support recovery and progress toward your goal."
)


def _get_model():
    """Configure and return the Gemini Flash model client, or None if unavailable."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY is not set; Gemini Flash calls will be skipped.")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(GEMINI_FLASH_MODEL)
    except Exception:
        logger.exception("Failed to initialize Gemini Flash model.")
        return None


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Generate a short, practical nutrition or recovery tip tailored to the
    user's fitness goal using Gemini Flash.
    """
    model = _get_model()
    if model is None:
        return _FALLBACK_TIP

    prompt = f"""
You are a nutrition coach. Give ONE short, practical nutrition or recovery
tip (2-3 sentences max) for someone whose fitness goal is: {goal}.

Keep it concise, actionable, and free of markdown formatting since it will
be shown as plain text on a webpage.
"""

    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else _FALLBACK_TIP
    except Exception:
        logger.exception("Gemini Flash nutrition tip generation failed.")
        return _FALLBACK_TIP
