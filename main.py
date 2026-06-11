"""
main.py — FastAPI backend for the Fitness Tracker application.
"""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from workout_tracker import (
    CardioExercise,
    Equipment,
    FitnessGoal,
    FitnessLevel,
    MuscleGroup,
    StrengthExercise,
    UserProfile,
    WorkoutGenerator,
    WorkoutLog,
    WorkoutSession,
    WorkoutType,
    EXERCISE_DATABASE,
)

app = FastAPI(title="Fitness Tracker API", version="3.0.0")
DATA_FILE = os.environ.get("DATA_FILE", "workouts.json")
log       = WorkoutLog(data_file=DATA_FILE)
generator = WorkoutGenerator()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ProfileCreate(BaseModel):
    name:         str
    age:          int              = Field(..., ge=13, le=100)
    level:        str
    goal:         str
    equipment:    list[str]        = []
    workout_days: int              = Field(default=3, ge=1, le=7)
    weight_kg:    Optional[float]  = Field(default=None, ge=20, le=500)
    height_cm:    Optional[float]  = Field(default=None, ge=100, le=250)


class ProfileUpdate(BaseModel):
    name:         Optional[str]       = None
    age:          Optional[int]       = Field(default=None, ge=13, le=100)
    level:        Optional[str]       = None
    goal:         Optional[str]       = None
    equipment:    Optional[list[str]] = None
    workout_days: Optional[int]       = Field(default=None, ge=1, le=7)
    weight_kg:    Optional[float]     = Field(default=None, ge=20, le=500)
    height_cm:    Optional[float]     = Field(default=None, ge=100, le=250)


class WeightLogRequest(BaseModel):
    weight_kg:  float = Field(..., ge=20, le=500)
    entry_date: Optional[str] = None


class SessionCreate(BaseModel):
    session_date: Optional[str] = None
    label:        str           = ""
    workout_type: str           = "full_body"
    user_id:      Optional[str] = None


class SessionUpdate(BaseModel):
    session_date: Optional[str] = None
    label:        Optional[str] = None
    workout_type: Optional[str] = None


class ExerciseCreate(BaseModel):
    type:         str
    name:         str
    muscle_group: str           = "Full Body"
    sets:         Optional[int]   = Field(default=None, ge=1)
    reps:         Optional[int]   = Field(default=None, ge=1)
    weight_kg:    Optional[float] = Field(default=None, ge=0)
    duration_min: Optional[float] = Field(default=None, gt=0)
    distance_km:  Optional[float] = Field(default=0.0, ge=0)
    notes:        str             = ""


class GenerateRequest(BaseModel):
    profile_id:    str
    workout_type:  str
    focus_muscles: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse("index.html")


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

@app.get("/meta/workout-types")
def get_workout_types():
    return [{"value": w.value, "label": w.value.replace("_", " ").title()} for w in WorkoutType]

@app.get("/meta/equipment")
def get_equipment():
    return [{"value": e.value, "label": e.value.replace("_", " ").title()} for e in Equipment]

@app.get("/meta/levels")
def get_levels():
    return [{"value": l.value, "label": l.value.title()} for l in FitnessLevel]

@app.get("/meta/goals")
def get_goals():
    return [{"value": g.value, "label": g.value.replace("_", " ").title()} for g in FitnessGoal]

@app.get("/meta/muscles")
def get_muscles():
    return [{"value": m.value, "label": m.value.replace("_", " ").title()} for m in MuscleGroup]

@app.get("/exercises/database")
def get_exercise_database(workout_type: Optional[str] = None, muscle: Optional[str] = None, equipment: Optional[str] = None, q: Optional[str] = None):
    results = EXERCISE_DATABASE
    if workout_type:
        results = [ex for ex in results if workout_type in ex.workout_types]
    if muscle:
        results = [ex for ex in results if ex.muscle_group == muscle]
    if equipment:
        results = [ex for ex in results if ex.equipment == equipment]
    if q:
        ql = q.lower()
        results = [ex for ex in results if ql in ex.name.lower() or ql in ex.muscle_group.lower()]
    return [ex.to_dict() for ex in results]


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

@app.get("/profiles")
def list_profiles():
    return [p.to_dict() for p in log.get_all_profiles()]

@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    p = log.get_profile(profile_id)
    if p is None:
        raise HTTPException(404, f"Profile '{profile_id}' not found.")
    return p.to_dict()

@app.post("/profiles", status_code=201)
def create_profile(body: ProfileCreate):
    try:
        profile = UserProfile(
            name=body.name, age=body.age, level=body.level, goal=body.goal,
            equipment=body.equipment, workout_days=body.workout_days,
            weight_kg=body.weight_kg, height_cm=body.height_cm,
        )
        if body.weight_kg:
            profile.log_weight(body.weight_kg)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    log.add_profile(profile)
    return profile.to_dict()

@app.put("/profiles/{profile_id}")
def update_profile(profile_id: str, body: ProfileUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    profile = log.update_profile(profile_id, **updates)
    if profile is None:
        raise HTTPException(404, f"Profile '{profile_id}' not found.")
    return profile.to_dict()

@app.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: str):
    if not log.delete_profile(profile_id):
        raise HTTPException(404, f"Profile '{profile_id}' not found.")
    return JSONResponse(204, content=None)

@app.post("/profiles/{profile_id}/weight")
def log_weight(profile_id: str, body: WeightLogRequest):
    """Log a body weight measurement for a user."""
    profile = log.get_profile(profile_id)
    if profile is None:
        raise HTTPException(404, f"Profile '{profile_id}' not found.")
    try:
        entry = profile.log_weight(body.weight_kg, body.entry_date)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    log._save()
    return {"entry": entry.to_dict(), "bmi": profile.bmi(), "bmi_category": profile.bmi_category()}

@app.get("/profiles/{profile_id}/weight")
def get_weight_history(profile_id: str):
    profile = log.get_profile(profile_id)
    if profile is None:
        raise HTTPException(404, f"Profile '{profile_id}' not found.")
    return {
        "history":       [e.to_dict() for e in profile.weight_history()],
        "current_weight": profile.weight_kg,
        "height_cm":      profile.height_cm,
        "bmi":            profile.bmi(),
        "bmi_category":   profile.bmi_category(),
        "weight_change":  profile.weight_change(),
    }


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

@app.post("/generate")
def generate_workout(body: GenerateRequest):
    profile = log.get_profile(body.profile_id)
    if profile is None:
        raise HTTPException(404, f"Profile '{body.profile_id}' not found.")
    try:
        template = generator.generate(profile=profile, workout_type=body.workout_type, focus_muscles=body.focus_muscles)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return template.to_dict()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@app.get("/sessions")
def list_sessions(user_id: Optional[str] = None):
    sessions = log.get_sessions_by_user(user_id) if user_id else log.get_all_sessions()
    return [s.to_dict() for s in sessions]

@app.get("/sessions/search")
def search_sessions(q: str = ""):
    return [s.to_dict() for s in log.search(q)]

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    s = log.get_session(session_id)
    if s is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return s.to_dict()

@app.post("/sessions", status_code=201)
def create_session(body: SessionCreate):
    try:
        session = WorkoutSession(session_date=body.session_date, label=body.label, workout_type=body.workout_type, user_id=body.user_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    log.add_session(session)
    return session.to_dict()

@app.put("/sessions/{session_id}")
def update_session(session_id: str, body: SessionUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    session = log.update_session(session_id, **updates)
    if session is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return session.to_dict()

@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str):
    if not log.delete_session(session_id):
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return JSONResponse(204, content=None)

@app.post("/sessions/{session_id}/exercises", status_code=201)
def add_exercise(session_id: str, body: ExerciseCreate):
    if log.get_session(session_id) is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    try:
        if body.type == "strength":
            if body.sets is None or body.reps is None or body.weight_kg is None:
                raise HTTPException(422, "Strength exercises require sets, reps, and weight_kg.")
            exercise = StrengthExercise(name=body.name, muscle_group=body.muscle_group, sets=body.sets, reps=body.reps, weight_kg=body.weight_kg, notes=body.notes)
        elif body.type == "cardio":
            if body.duration_min is None:
                raise HTTPException(422, "Cardio exercises require duration_min.")
            exercise = CardioExercise(name=body.name, muscle_group=body.muscle_group, duration_min=body.duration_min, distance_km=body.distance_km or 0.0, notes=body.notes)
        else:
            raise HTTPException(422, f"Unknown type '{body.type}'.")
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return log.add_exercise_to_session(session_id, exercise).to_dict()

@app.delete("/sessions/{session_id}/exercises/{exercise_id}", status_code=204)
def remove_exercise(session_id: str, exercise_id: str):
    if log.get_session(session_id) is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    if not log.remove_exercise_from_session(session_id, exercise_id):
        raise HTTPException(404, f"Exercise '{exercise_id}' not found.")
    return JSONResponse(204, content=None)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/stats")
def get_stats():
    sessions     = log.get_all_sessions()
    total_volume = sum(s.total_volume() for s in sessions)
    total_cardio = sum(s.total_cardio_minutes() for s in sessions)
    return {
        "total_sessions":       log.total_sessions(),
        "total_profiles":       len(log.get_all_profiles()),
        "total_volume_kg":      round(total_volume, 2),
        "total_cardio_minutes": round(total_cardio, 1),
    }
