"""
FitBuddy - AI Fitness Plan Generator using Gemini Models.

FastAPI application entry point.
"""

import os
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.database import init_db
from app.routes import router

# Load environment variables from a .env file if present.
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitbuddy.main")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description="Generates personalized workout plans and nutrition tips using Gemini models.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(router)


@app.on_event("startup")
def on_startup():
    """Initialize the database tables on application startup."""
    init_db()
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning(
            "GOOGLE_API_KEY is not set. Set it in your .env file to enable "
            "real AI-generated plans; fallback text will be used otherwise."
        )
