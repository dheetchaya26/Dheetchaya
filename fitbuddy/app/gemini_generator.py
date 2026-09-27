"""
Workout plan generation and feedback-based updates using Gemini 1.5 Pro.
"""

import os
import logging

import google.generativeai as genai

logger = logging.getLogger("fitbuddy.gemini_generator")

GEMINI_PRO_MODEL = "gemini-1.5-pro"

_FALLBACK_PLAN = (
    "We couldn't generate your workout plan right now because the AI "
    "service did not respond. Please try again in a moment. In the "
    "meantime, here is a safe general routine:\n\n"
    "Day 1: Full body strength (30 min)\n"
    "Day 2: Cardio - brisk walk or cycling (30 min)\n"
    "Day 3: Rest / light stretching\n"
    "Day 4: Upper body strength (30 min)\n"
    "Day 5: Lower body strength (30 min)\n"
    "Day 6: Cardio + core (30 min)\n"
    "Day 7: Rest / recovery"
)


def _get_model():
    """Configure and return the Gemini Pro model client, or None if unavailable."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY is not set; Gemini Pro calls will be skipped.")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(GEMINI_PRO_MODEL)
    except Exception:
        logger.exception("Failed to initialize Gemini Pro model.")
        return None


def generate_workout_gemini(goal: str, intensity: str, age: int = None, weight: float = None) -> str:
    """
    Generate a structured 7-day workout plan tailored to the user's goal
    and intensity preference using Gemini 1.5 Pro.
    """
    model = _get_model()
    if model is None:
        return _FALLBACK_PLAN

    prompt = f"""
You are a certified fitness coach. Create a personalized 7-day workout plan.

User profile:
- Fitness goal: {goal}
- Preferred workout intensity: {intensity}
- Age: {age if age else "not specified"}
- Weight: {weight if weight else "not specified"} kg

Instructions:
- Structure the plan day by day (Day 1 through Day 7).
- Each day must include: a short focus title (e.g. "Upper Body Strength",
  "Active Recovery"), a brief warm-up (5-10 minutes), the main workout with
  specific exercises and sets/reps or duration, and a short cooldown or
  recovery note.
- Match the difficulty to the requested intensity level.
- Include at least one rest or active-recovery day.
- Keep the formatting clean, plain text, easy to read (no markdown tables,
  no asterisks) since it will be shown inside a <pre> block on a webpage.
"""

    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else _FALLBACK_PLAN
    except Exception:
        logger.exception("Gemini Pro workout generation failed.")
        return _FALLBACK_PLAN


def update_workout_plan(original_plan: str, feedback: str) -> str:
    """
    Revise an existing workout plan based on free-text user feedback,
    using Gemini 1.5 Pro.
    """
    model = _get_model()
    if model is None:
        return original_plan or _FALLBACK_PLAN

    prompt = f"""
You are a certified fitness coach. A user wants their existing 7-day workout
plan revised based on their feedback.

Original plan:
{original_plan}

User feedback:
{feedback}

Instructions:
- Update the plan to reflect the user's feedback while keeping the overall
  7-day structure.
- Keep the same clean, plain-text, day-by-day format as the original
  (Day 1 through Day 7, with warm-up, main workout, cooldown/recovery note).
- Do not include markdown tables or asterisks, since this will be displayed
  inside a <pre> block on a webpage.
"""

    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else (original_plan or _FALLBACK_PLAN)
    except Exception:
        logger.exception("Gemini Pro plan update failed.")
        return original_plan or _FALLBACK_PLAN
