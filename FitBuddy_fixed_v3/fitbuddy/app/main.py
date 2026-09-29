"""
FitBuddy - AI Fitness Plan Generator.
FastAPI application entry point.
"""

import os
import logging

from dotenv import load_dotenv

# Load .env before importing modules that may use environment variables.
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitbuddy.main")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images"), exist_ok=True)

app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description="Generates personalized workout plans and nutrition tips using Gemini models.",
    version="1.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        logger.warning(
            "Gemini API key is not set. The app will run using fallback demo text."
        )
    else:
        logger.info("Gemini API key detected.")


@app.get("/health")
def health():
    return {"status": "ok", "app": "FitBuddy"}
