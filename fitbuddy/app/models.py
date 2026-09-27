"""
Pydantic schemas used across the FitBuddy application.
"""

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """Represents the data captured from the home page form."""

    username: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., gt=0, lt=120)
    weight: float = Field(..., gt=0, lt=500)
    goal: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)


class FeedbackRequest(BaseModel):
    """Represents the data captured from the feedback form."""

    user_id: str = Field(..., min_length=1, max_length=50)
    feedback: str = Field(..., min_length=1)
