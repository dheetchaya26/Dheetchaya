"""
Workout plan generation and feedback-based updates using the current Google GenAI SDK.
"""

import os
import logging

from google import genai
from google.genai import types

logger = logging.getLogger("fitbuddy.gemini_generator")

GEMINI_WORKOUT_MODEL = "gemini-3.8-flash"
API_TIMEOUT_MS = 25000

_FALLBACK_PLAN = (
    "AI generation is temporarily unavailable, so FitBuddy is showing a safe demo plan.\n\n"
    "Day 1: Full body strength - 30 minutes\n"
    "Day 2: Brisk walking or cycling - 30 minutes\n"
    "Day 3: Rest and light stretching\n"
    "Day 4: Upper body strength - 30 minutes\n"
    "Day 5: Lower body strength - 30 minutes\n"
    "Day 6: Cardio and core - 30 minutes\n"
    "Day 7: Rest and recovery"
)


def _get_client():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found; fallback workout plan will be used.")
        return None

    try:
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=API_TIMEOUT_MS),
        )
    except Exception:
        logger.exception("Failed to initialize Gemini client.")
        return None


def generate_workout_gemini(
    goal: str,
    intensity: str,
    age: int = None,
    weight: float = None,
) -> str:
    client = _get_client()
    if client is None:
        return _FALLBACK_PLAN

    prompt = f"""
You are a fitness planning assistant. Create a practical 7-day workout plan.

User profile:
Fitness goal: {goal}
Workout intensity: {intensity}
Age: {age if age is not None else "not specified"}
Weight: {weight if weight is not None else "not specified"} kg

Requirements:
- Day 1 through Day 7.
- Include a short focus title for each day.
- Include a 5-10 minute warm-up.
- Include the main workout with exercises and sets/reps or duration.
- Include a cooldown or recovery note.
- Include at least one rest or active-recovery day.
- Match the requested intensity.
- Keep the answer plain text and easy to read.
- Do not use markdown tables.
"""

    try:
        logger.info("Calling Gemini for workout generation...")
        response = client.models.generate_content(
            model=GEMINI_WORKOUT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1400,
                temperature=0.5,
            ),
        )
        text = (response.text or "").strip()
        logger.info("Workout generation completed.")
        return text if text else _FALLBACK_PLAN
    except Exception:
        logger.exception("Gemini workout generation failed; using fallback.")
        return _FALLBACK_PLAN


def update_workout_plan(original_plan: str, feedback: str) -> str:
    client = _get_client()
    if client is None:
        return original_plan or _FALLBACK_PLAN

    prompt = f"""
You are a fitness planning assistant.

Original 7-day workout plan:
{original_plan}

User feedback:
{feedback}

Revise the plan to follow the feedback while keeping a complete Day 1 through Day 7 structure.
Keep the answer plain text and easy to read. Do not use markdown tables.
"""

    try:
        logger.info("Calling Gemini to update workout plan...")
        response = client.models.generate_content(
            model=GEMINI_WORKOUT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1400,
                temperature=0.5,
            ),
        )
        text = (response.text or "").strip()
        logger.info("Workout update completed.")
        return text if text else (original_plan or _FALLBACK_PLAN)
    except Exception:
        logger.exception("Gemini workout update failed; keeping existing plan.")
        return original_plan or _FALLBACK_PLAN
