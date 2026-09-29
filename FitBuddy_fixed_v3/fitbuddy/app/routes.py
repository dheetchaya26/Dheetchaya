"""
Route definitions for FitBuddy.
"""

import os
import logging
import asyncio

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.models import UserInput, FeedbackRequest
from app.gemini_generator import generate_workout_gemini, update_workout_plan
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.database import (
    save_user,
    save_plan,
    update_plan,
    get_user,
    get_original_plan,
    get_all_users,
)

logger = logging.getLogger("fitbuddy.routes")

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

WORKOUT_TIMEOUT_SECONDS = 35
TIP_TIMEOUT_SECONDS = 30

_TIMEOUT_PLAN = (
    "The AI request took too long, so FitBuddy returned a demo plan instead.\n\n"
    "Day 1: Full body strength - 30 minutes\n"
    "Day 2: Brisk walking or cycling - 30 minutes\n"
    "Day 3: Rest and light stretching\n"
    "Day 4: Upper body strength - 30 minutes\n"
    "Day 5: Lower body strength - 30 minutes\n"
    "Day 6: Cardio and core - 30 minutes\n"
    "Day 7: Rest and recovery"
)

_TIMEOUT_TIP = (
    "The nutrition AI request timed out. Stay hydrated and choose balanced meals "
    "with suitable protein, carbohydrates, fruits or vegetables."
)


async def _run_workout_with_timeout(**kwargs):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(generate_workout_gemini, **kwargs),
            timeout=WORKOUT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("Workout generation exceeded %s seconds.", WORKOUT_TIMEOUT_SECONDS)
        return _TIMEOUT_PLAN


async def _run_tip_with_timeout(goal: str):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(generate_nutrition_tip_with_flash, goal),
            timeout=TIP_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("Nutrition generation exceeded %s seconds.", TIP_TIMEOUT_SECONDS)
        return _TIMEOUT_TIP


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    try:
        user_input = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
    except ValidationError as exc:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Invalid input: {exc}"},
        )

    logger.info("Generating plan for user_id=%s", user_input.user_id)

    workout_plan, nutrition_tip = await asyncio.gather(
        _run_workout_with_timeout(
            goal=user_input.goal,
            intensity=user_input.intensity,
            age=user_input.age,
            weight=user_input.weight,
        ),
        _run_tip_with_timeout(user_input.goal),
    )

    save_user(
        user_id=user_input.user_id,
        username=user_input.username,
        age=user_input.age,
        weight=user_input.weight,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )
    save_plan(
        user_id=user_input.user_id,
        workout_plan=workout_plan,
        nutrition_tip=nutrition_tip,
    )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "username": user_input.username,
            "user_id": user_input.user_id,
            "age": user_input.age,
            "weight": user_input.weight,
            "goal": user_input.goal,
            "intensity": user_input.intensity,
            "workout_plan": workout_plan,
            "nutrition_tip": nutrition_tip,
            "updated": False,
        },
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
):
    try:
        FeedbackRequest(user_id=user_id, feedback=feedback)
    except ValidationError as exc:
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "error": f"Invalid feedback: {exc}"},
        )

    user = get_user(user_id)
    if user is None:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": f"No user found with User ID '{user_id}'. Please generate a plan first.",
            },
        )

    original_plan = get_original_plan(user_id)

    try:
        revised_plan = await asyncio.wait_for(
            asyncio.to_thread(
                update_workout_plan,
                original_plan=original_plan,
                feedback=feedback,
            ),
            timeout=WORKOUT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("Feedback update exceeded %s seconds.", WORKOUT_TIMEOUT_SECONDS)
        revised_plan = original_plan or _TIMEOUT_PLAN

    update_plan(user_id=user_id, updated_plan=revised_plan)

    nutrition_tip = user.nutrition_tip
    if not nutrition_tip:
        nutrition_tip = await _run_tip_with_timeout(user.goal)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "username": user.username,
            "user_id": user.user_id,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "workout_plan": revised_plan,
            "nutrition_tip": nutrition_tip,
            "updated": True,
        },
    )


@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(request: Request):
    users = get_all_users()
    return templates.TemplateResponse(
        "all_users.html",
        {"request": request, "users": users},
    )
