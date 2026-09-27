# FitBuddy – AI Fitness Plan Generator using Gemini Models

FitBuddy is a FastAPI web app that generates personalized 7-day workout
plans and nutrition/recovery tips using Google's Gemini models, based on a
user's fitness goal, age, weight, and workout intensity. Users can submit
feedback to regenerate their plan, and admins can view all users and their
plans on a dashboard.

## Tech Stack
- **Backend:** FastAPI
- **AI:** Gemini 1.5 Pro (workout plans + feedback updates), Gemini Flash (nutrition tips)
- **Database:** SQLite + SQLAlchemy
- **Frontend:** HTML, CSS, Jinja2 templates
- **Server:** Uvicorn

## Project Structure
```
fitbuddy/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── routes.py                  # All route handlers
│   ├── models.py                  # Pydantic schemas
│   ├── database.py                # SQLAlchemy models + CRUD helpers
│   ├── gemini_generator.py        # Gemini 1.5 Pro: workout plan + updates
│   └── gemini_flash_generator.py  # Gemini Flash: nutrition tips
├── templates/
│   ├── index.html                 # Input form
│   ├── result.html                # Plan, tip, feedback form
│   └── all_users.html             # Admin dashboard
├── static/images/                 # Static assets
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & Run Locally

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your Gemini API key**
   - Copy `.env.example` to `.env`
   - Get a free key from https://aistudio.google.com/app/apikey
   - Paste it into `.env`:
     ```
     GOOGLE_API_KEY=your_actual_key_here
     ```

4. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open the app**
   - App: http://127.0.0.1:8000
   - API docs (Swagger): http://127.0.0.1:8000/docs
   - Admin dashboard: http://127.0.0.1:8000/view-all-users

## Notes
- If `GOOGLE_API_KEY` is missing or a Gemini call fails, the app falls
  back to a safe default workout plan / nutrition tip instead of crashing,
  so the app always keeps working end-to-end.
- The SQLite database file (`fitbuddy.db`) is created automatically on
  first run in the project root.
- Both the original plan and any feedback-updated plan are stored
  separately per user, so the admin dashboard can show the before/after.

## Testing Checklist
- [ ] Submitting the home page form returns a 7-day plan + nutrition tip
- [ ] Submitting feedback on `/submit-feedback` updates the plan and shows a confirmation
- [ ] `/view-all-users` lists all users with original and updated plans
- [ ] `/docs` loads and each endpoint is testable from Swagger UI
