"""
Route definitions for FitBuddy.
"""

import os
import logging

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


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home route - displays the user input form."""
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
    """Process user input, generate the workout plan + nutrition tip, and store them."""
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

    workout_plan = generate_workout_gemini(
        goal=user_input.goal,
        intensity=user_input.intensity,
        age=user_input.age,
        weight=user_input.weight,
    )
    nutrition_tip = generate_nutrition_tip_with_flash(goal=user_input.goal)

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
    """Update an existing user's workout plan based on their feedback."""
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
            {"request": request, "error": f"No user found with User ID '{user_id}'. Please generate a plan first."},
        )

    original_plan = get_original_plan(user_id)
    revised_plan = update_workout_plan(original_plan=original_plan, feedback=feedback)
    update_plan(user_id=user_id, updated_plan=revised_plan)

    # Refresh nutrition tip in case the user's goal-related context changed.
    nutrition_tip = user.nutrition_tip or generate_nutrition_tip_with_flash(goal=user.goal)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "username": user.username,
            "user_id": user.user_id,
            "goal": user.goal,
            "intensity": user.intensity,
            "workout_plan": revised_plan,
            "nutrition_tip": nutrition_tip,
            "updated": True,
        },
    )


@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(request: Request):
    """Admin dashboard - shows every registered user and their plans."""
    users = get_all_users()
    return templates.TemplateResponse(
        "all_users.html",
        {"request": request, "users": users},
    )
