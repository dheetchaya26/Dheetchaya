"""
Database layer for FitBuddy.

Uses SQLAlchemy ORM with a SQLite backend to persist user details along
with their original and feedback-updated workout plans.
"""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fitbuddy.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """A single FitBuddy user and their stored plans."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(100), nullable=False)
    intensity = Column(String(50), nullable=False)
    nutrition_tip = Column(Text, nullable=True)
    original_plan = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Return a new database session. Caller is responsible for closing it."""
    return SessionLocal()


# ---------------------------------------------------------------------------
# CRUD helper functions
# ---------------------------------------------------------------------------

def save_user(user_id: str, username: str, age: int, weight: float, goal: str, intensity: str):
    """Create a new user record, or update basic details if it already exists."""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            user = User(
                user_id=user_id,
                username=username,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity,
            )
            db.add(user)
        else:
            user.username = username
            user.age = age
            user.weight = weight
            user.goal = goal
            user.intensity = intensity
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def save_plan(user_id: str, workout_plan: str, nutrition_tip: str):
    """Save the freshly generated workout plan and nutrition tip for a user."""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise ValueError(f"No user found with user_id={user_id}")
        user.original_plan = workout_plan
        user.nutrition_tip = nutrition_tip
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def update_plan(user_id: str, updated_plan: str):
    """Store the feedback-revised plan separately from the original plan."""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise ValueError(f"No user found with user_id={user_id}")
        user.updated_plan = updated_plan
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user(user_id: str):
    """Fetch a single user by their user_id."""
    db = get_db_session()
    try:
        return db.query(User).filter(User.user_id == user_id).first()
    finally:
        db.close()


def get_original_plan(user_id: str):
    """Return only the original plan text for a given user."""
    user = get_user(user_id)
    return user.original_plan if user else None


def get_all_users():
    """Return every user record, most recently created first."""
    db = get_db_session()
    try:
        return db.query(User).order_by(User.created_at.desc()).all()
    finally:
        db.close()


def get_all_plans():
    """Alias kept for readability where callers only care about plans."""
    return get_all_users()
