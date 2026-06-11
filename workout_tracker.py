"""
workout_tracker.py
Core OOP module for the Fitness Tracker application.

Class hierarchy:
    Exercise (ABC)
    ├── StrengthExercise      — sets, reps, weight_kg
    └── CardioExercise        — duration_min, distance_km

    UserProfile               — user characteristics (level, goal, equipment)
    ExerciseTemplate          — a blueprint exercise from the database
    WorkoutTemplate           — a generated workout plan (list of templates)
    WorkoutGenerator          — generates WorkoutTemplate from UserProfile
    WorkoutSession            — a logged training session (completed workout)
    WorkoutLog                — all sessions, main CRUD container + persistence
"""

from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FitnessLevel(str, Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


class FitnessGoal(str, Enum):
    STRENGTH    = "strength"
    WEIGHT_LOSS = "weight_loss"
    ENDURANCE   = "endurance"
    MUSCLE_GAIN = "muscle_gain"


class WorkoutType(str, Enum):
    HOME      = "home"
    SPLIT     = "split"
    FULL_BODY = "full_body"
    CARDIO    = "cardio"


class Equipment(str, Enum):
    BODYWEIGHT    = "bodyweight"
    DUMBBELL      = "dumbbell"
    BARBELL       = "barbell"
    MACHINE       = "machine"
    CABLE         = "cable"
    CARDIO_MACHINE = "cardio_machine"
    RESISTANCE_BAND = "resistance_band"
    KETTLEBELL    = "kettlebell"


class MuscleGroup(str, Enum):
    CHEST      = "chest"
    BACK       = "back"
    SHOULDERS  = "shoulders"
    BICEPS     = "biceps"
    TRICEPS    = "triceps"
    LEGS       = "legs"
    GLUTES     = "glutes"
    CORE       = "core"
    FULL_BODY  = "full_body"
    CARDIO     = "cardio"


# ---------------------------------------------------------------------------
# Abstract base class — Exercise
# ---------------------------------------------------------------------------

class Exercise(ABC):
    """Abstract base class for all exercise types.

    Subclasses must implement:
        get_type()         → str
        get_extra_fields() → dict

    Shared validation (name, muscle_group, notes) lives here so subclasses
    never have to re-implement it.
    """

    def __init__(
        self,
        name: str,
        muscle_group: str,
        notes: str = "",
        _id: Optional[str] = None,
    ) -> None:
        self._id: str = _id if _id else str(uuid.uuid4())
        self.name         = name
        self.muscle_group = muscle_group
        self.notes        = notes

    @property
    def id(self) -> str:
        """Unique identifier — read-only after creation."""
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Exercise name cannot be empty.")
        self._name = value

    @property
    def muscle_group(self) -> str:
        return self._muscle_group

    @muscle_group.setter
    def muscle_group(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Muscle group cannot be empty.")
        self._muscle_group = value

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, value: str) -> None:
        self._notes = value.strip()

    @abstractmethod
    def get_type(self) -> str:
        """Return a string identifying the concrete exercise type."""

    @abstractmethod
    def get_extra_fields(self) -> dict:
        """Return type-specific fields for serialisation."""

    def to_dict(self) -> dict:
        """Serialise the exercise to a plain dictionary."""
        base = {
            "id":           self._id,
            "type":         self.get_type(),
            "name":         self._name,
            "muscle_group": self._muscle_group,
            "notes":        self._notes,
        }
        base.update(self.get_extra_fields())
        return base

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id!r}, "
            f"name={self._name!r}, muscle_group={self._muscle_group!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Exercise):
            return NotImplemented
        return self._id == other._id


# ---------------------------------------------------------------------------
# Concrete exercise types
# ---------------------------------------------------------------------------

class StrengthExercise(Exercise):
    """A weight-training exercise defined by sets, reps, and weight."""

    def __init__(
        self,
        name: str,
        muscle_group: str,
        sets: int,
        reps: int,
        weight_kg: float,
        notes: str = "",
        _id: Optional[str] = None,
    ) -> None:
        super().__init__(name, muscle_group, notes, _id)
        self.sets      = sets
        self.reps      = reps
        self.weight_kg = weight_kg

    @property
    def sets(self) -> int:
        return self._sets

    @sets.setter
    def sets(self, value: int) -> None:
        value = int(value)
        if value < 1:
            raise ValueError("Sets must be at least 1.")
        self._sets = value

    @property
    def reps(self) -> int:
        return self._reps

    @reps.setter
    def reps(self, value: int) -> None:
        value = int(value)
        if value < 1:
            raise ValueError("Reps must be at least 1.")
        self._reps = value

    @property
    def weight_kg(self) -> float:
        return self._weight_kg

    @weight_kg.setter
    def weight_kg(self, value: float) -> None:
        value = float(value)
        if value < 0:
            raise ValueError("Weight cannot be negative.")
        self._weight_kg = round(value, 2)

    def get_type(self) -> str:
        return "strength"

    def get_extra_fields(self) -> dict:
        return {
            "sets":      self._sets,
            "reps":      self._reps,
            "weight_kg": self._weight_kg,
        }

    def total_volume(self) -> float:
        """Return total volume lifted: sets × reps × weight_kg."""
        return self._sets * self._reps * self._weight_kg


class CardioExercise(Exercise):
    """A cardiovascular exercise defined by duration and optional distance."""

    def __init__(
        self,
        name: str,
        muscle_group: str,
        duration_min: float,
        distance_km: float = 0.0,
        notes: str = "",
        _id: Optional[str] = None,
    ) -> None:
        super().__init__(name, muscle_group, notes, _id)
        self.duration_min = duration_min
        self.distance_km  = distance_km

    @property
    def duration_min(self) -> float:
        return self._duration_min

    @duration_min.setter
    def duration_min(self, value: float) -> None:
        value = float(value)
        if value <= 0:
            raise ValueError("Duration must be greater than 0.")
        self._duration_min = round(value, 1)

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @distance_km.setter
    def distance_km(self, value: float) -> None:
        value = float(value)
        if value < 0:
            raise ValueError("Distance cannot be negative.")
        self._distance_km = round(value, 2)

    def get_type(self) -> str:
        return "cardio"

    def get_extra_fields(self) -> dict:
        return {
            "duration_min": self._duration_min,
            "distance_km":  self._distance_km,
        }

    def pace_min_per_km(self) -> Optional[float]:
        """Return pace in min/km, or None if distance is 0."""
        if self._distance_km == 0:
            return None
        return round(self._duration_min / self._distance_km, 2)


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------

def exercise_from_dict(data: dict) -> Exercise:
    """Reconstruct an Exercise object from a serialised dictionary."""
    ex_type = data.get("type")
    if ex_type == "strength":
        return StrengthExercise(
            name=data["name"],
            muscle_group=data["muscle_group"],
            sets=data["sets"],
            reps=data["reps"],
            weight_kg=data["weight_kg"],
            notes=data.get("notes", ""),
            _id=data.get("id"),
        )
    if ex_type == "cardio":
        return CardioExercise(
            name=data["name"],
            muscle_group=data["muscle_group"],
            duration_min=data["duration_min"],
            distance_km=data.get("distance_km", 0.0),
            notes=data.get("notes", ""),
            _id=data.get("id"),
        )
    raise ValueError(f"Unknown exercise type: {ex_type!r}")


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class WeightEntry:
    """A single body-weight measurement on a given date.

    Args:
        weight_kg:  Body weight in kilograms (20–500).
        entry_date: Date of measurement in YYYY-MM-DD format.
    """

    def __init__(self, weight_kg: float, entry_date: Optional[str] = None) -> None:
        self.weight_kg  = weight_kg
        self.entry_date = entry_date or date.today().isoformat()

    @property
    def weight_kg(self) -> float:
        return self._weight_kg

    @weight_kg.setter
    def weight_kg(self, value: float) -> None:
        value = float(value)
        if not (20.0 <= value <= 500.0):
            raise ValueError("Body weight must be between 20 and 500 kg.")
        self._weight_kg = round(value, 1)

    @property
    def entry_date(self) -> str:
        return self._entry_date

    @entry_date.setter
    def entry_date(self, value: str) -> None:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("entry_date must be in YYYY-MM-DD format.")
        self._entry_date = value

    def to_dict(self) -> dict:
        return {"weight_kg": self._weight_kg, "entry_date": self._entry_date}

    @classmethod
    def from_dict(cls, data: dict) -> "WeightEntry":
        return cls(weight_kg=data["weight_kg"], entry_date=data.get("entry_date"))

    def __repr__(self) -> str:
        return f"WeightEntry({self._weight_kg} kg on {self._entry_date})"


class UserProfile:
    """Stores a user's fitness characteristics used for workout generation.

    Args:
        name:          Display name.
        age:           Age in years (13–100).
        level:         FitnessLevel enum value.
        goal:          FitnessGoal enum value.
        equipment:     List of Equipment the user has access to.
        workout_days:  How many days per week the user trains (1–7).
        weight_kg:     Current body weight in kg (optional).
        height_cm:     Height in centimetres (optional, 100–250).
        weight_history: List of WeightEntry dicts from persistence.
        _id:           Internal — used when reconstructing from JSON.
    """

    def __init__(
        self,
        name: str,
        age: int,
        level: str,
        goal: str,
        equipment: list[str],
        workout_days: int = 3,
        weight_kg: Optional[float] = None,
        height_cm: Optional[float] = None,
        weight_history: Optional[list[dict]] = None,
        _id: Optional[str] = None,
    ) -> None:
        self._id             = _id if _id else str(uuid.uuid4())
        self.name            = name
        self.age             = age
        self.level           = level
        self.goal            = goal
        self.equipment       = equipment
        self.workout_days    = workout_days
        self.weight_kg       = weight_kg
        self.height_cm       = height_cm
        self._weight_history: list[WeightEntry] = []
        for entry in (weight_history or []):
            self._weight_history.append(WeightEntry.from_dict(entry))

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        value = int(value)
        if not (13 <= value <= 100):
            raise ValueError("Age must be between 13 and 100.")
        self._age = value

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, value: str) -> None:
        try:
            self._level = FitnessLevel(value).value
        except ValueError:
            raise ValueError(
                f"Invalid level '{value}'. Choose: "
                + ", ".join(l.value for l in FitnessLevel)
            )

    @property
    def goal(self) -> str:
        return self._goal

    @goal.setter
    def goal(self, value: str) -> None:
        try:
            self._goal = FitnessGoal(value).value
        except ValueError:
            raise ValueError(
                f"Invalid goal '{value}'. Choose: "
                + ", ".join(g.value for g in FitnessGoal)
            )

    @property
    def equipment(self) -> list[str]:
        return list(self._equipment)

    @equipment.setter
    def equipment(self, value: list[str]) -> None:
        validated = []
        for item in value:
            try:
                validated.append(Equipment(item).value)
            except ValueError:
                raise ValueError(
                    f"Invalid equipment '{item}'. Choose: "
                    + ", ".join(e.value for e in Equipment)
                )
        self._equipment = validated

    @property
    def workout_days(self) -> int:
        return self._workout_days

    @workout_days.setter
    def workout_days(self, value: int) -> None:
        value = int(value)
        if not (1 <= value <= 7):
            raise ValueError("Workout days must be between 1 and 7.")
        self._workout_days = value

    @property
    def weight_kg(self) -> Optional[float]:
        return self._weight_kg

    @weight_kg.setter
    def weight_kg(self, value: Optional[float]) -> None:
        if value is None:
            self._weight_kg = None
            return
        value = float(value)
        if not (20.0 <= value <= 500.0):
            raise ValueError("Body weight must be between 20 and 500 kg.")
        self._weight_kg = round(value, 1)

    @property
    def height_cm(self) -> Optional[float]:
        return self._height_cm

    @height_cm.setter
    def height_cm(self, value: Optional[float]) -> None:
        if value is None:
            self._height_cm = None
            return
        value = float(value)
        if not (100.0 <= value <= 250.0):
            raise ValueError("Height must be between 100 and 250 cm.")
        self._height_cm = round(value, 1)

    # --- BMI ---

    def bmi(self) -> Optional[float]:
        """Return BMI if both weight and height are set, otherwise None."""
        if self._weight_kg is None or self._height_cm is None:
            return None
        height_m = self._height_cm / 100
        return round(self._weight_kg / (height_m ** 2), 1)

    def bmi_category(self) -> Optional[str]:
        """Return BMI category string, or None if BMI cannot be calculated."""
        b = self.bmi()
        if b is None:
            return None
        if b < 18.5:
            return "underweight"
        if b < 25.0:
            return "normal"
        if b < 30.0:
            return "overweight"
        return "obese"

    # --- Weight history ---

    def log_weight(self, weight_kg: float, entry_date: Optional[str] = None) -> WeightEntry:
        """Add a body-weight measurement and update current weight."""
        entry = WeightEntry(weight_kg=weight_kg, entry_date=entry_date)
        self._weight_history.append(entry)
        self._weight_kg = entry.weight_kg
        return entry

    def weight_history(self) -> list[WeightEntry]:
        """Return weight entries sorted oldest → newest."""
        return sorted(self._weight_history, key=lambda e: e.entry_date)

    def weight_change(self) -> Optional[float]:
        """Return total weight change (latest - earliest) or None if < 2 entries."""
        history = self.weight_history()
        if len(history) < 2:
            return None
        return round(history[-1].weight_kg - history[0].weight_kg, 1)

    # --- Equipment helper ---

    def has_equipment(self, eq: str) -> bool:
        """Return True if the user has access to the given equipment."""
        return eq in self._equipment

    def to_dict(self) -> dict:
        return {
            "id":             self._id,
            "name":           self._name,
            "age":            self._age,
            "level":          self._level,
            "goal":           self._goal,
            "equipment":      self._equipment,
            "workout_days":   self._workout_days,
            "weight_kg":      self._weight_kg,
            "height_cm":      self._height_cm,
            "weight_history": [e.to_dict() for e in self._weight_history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            name=data["name"],
            age=data["age"],
            level=data["level"],
            goal=data["goal"],
            equipment=data.get("equipment", []),
            workout_days=data.get("workout_days", 3),
            weight_kg=data.get("weight_kg"),
            height_cm=data.get("height_cm"),
            weight_history=data.get("weight_history", []),
            _id=data.get("id"),
        )

    def __repr__(self) -> str:
        return (
            f"UserProfile(name={self._name!r}, level={self._level!r}, "
            f"goal={self._goal!r}, bmi={self.bmi()!r})"
        )


# ---------------------------------------------------------------------------
# ExerciseTemplate — blueprint exercise from the database
# ---------------------------------------------------------------------------

class ExerciseTemplate:
    """A blueprint exercise that can be included in a generated workout plan.

    Unlike Exercise (which represents a logged set), ExerciseTemplate
    represents a *recommended* exercise with suggested parameters.

    Args:
        name:            Exercise name.
        muscle_group:    Primary muscle group (MuscleGroup enum value).
        exercise_type:   'strength' or 'cardio'.
        equipment:       Equipment required (Equipment enum value).
        workout_types:   Which WorkoutType categories this exercise fits.
        levels:          Which FitnessLevel values this exercise suits.
        default_sets:    Suggested sets (strength only).
        default_reps:    Suggested reps (strength only).
        default_duration_min: Suggested duration (cardio only).
        description:     Brief coaching cue.
    """

    def __init__(
        self,
        name: str,
        muscle_group: str,
        exercise_type: str,
        equipment: str,
        workout_types: list[str],
        levels: list[str],
        default_sets: int = 3,
        default_reps: int = 10,
        default_duration_min: float = 20.0,
        description: str = "",
    ) -> None:
        self.name                 = name
        self.muscle_group         = muscle_group
        self.exercise_type        = exercise_type
        self.equipment            = equipment
        self.workout_types        = workout_types
        self.levels               = levels
        self.default_sets         = default_sets
        self.default_reps         = default_reps
        self.default_duration_min = default_duration_min
        self.description          = description

    def fits(self, workout_type: str, level: str, user_equipment: list[str]) -> bool:
        """Return True if this template suits the given workout type, level, and equipment."""
        return (
            workout_type in self.workout_types
            and level in self.levels
            and self.equipment in user_equipment
        )

    def to_dict(self) -> dict:
        return {
            "name":                 self.name,
            "muscle_group":         self.muscle_group,
            "exercise_type":        self.exercise_type,
            "equipment":            self.equipment,
            "workout_types":        self.workout_types,
            "levels":               self.levels,
            "default_sets":         self.default_sets,
            "default_reps":         self.default_reps,
            "default_duration_min": self.default_duration_min,
            "description":          self.description,
        }

    def __repr__(self) -> str:
        return (
            f"ExerciseTemplate(name={self.name!r}, "
            f"muscle={self.muscle_group!r}, eq={self.equipment!r})"
        )


# ---------------------------------------------------------------------------
# Exercise database
# ---------------------------------------------------------------------------

EXERCISE_DATABASE: list[ExerciseTemplate] = [
    # ── CHEST ────────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Barbell Bench Press", MuscleGroup.CHEST.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=8,
        description="Lie flat, grip just outside shoulder width, lower to chest and press up.",
    ),
    ExerciseTemplate(
        "Dumbbell Bench Press", MuscleGroup.CHEST.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=10,
        description="Control the dumbbells on the way down, press up and slightly inward.",
    ),
    ExerciseTemplate(
        "Push-Up", MuscleGroup.CHEST.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.FULL_BODY.value, WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Keep body straight from head to heels. Lower chest to floor, push back up.",
    ),
    ExerciseTemplate(
        "Cable Chest Fly", MuscleGroup.CHEST.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Set cables at chest height. Keep slight bend in elbows, bring hands together.",
    ),
    ExerciseTemplate(
        "Chest Press Machine", MuscleGroup.CHEST.value, "strength",
        Equipment.MACHINE.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=12,
        description="Adjust seat so handles are at chest height. Press forward and control back.",
    ),

    # ── BACK ─────────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Pull-Up", MuscleGroup.BACK.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=6,
        description="Dead hang, pull chest toward bar, lower with control.",
    ),
    ExerciseTemplate(
        "Barbell Bent-Over Row", MuscleGroup.BACK.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=8,
        description="Hinge at hips, pull bar to lower chest, squeeze shoulder blades.",
    ),
    ExerciseTemplate(
        "Dumbbell Single-Arm Row", MuscleGroup.BACK.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Support on bench, pull dumbbell to hip, keep elbow close to body.",
    ),
    ExerciseTemplate(
        "Lat Pulldown", MuscleGroup.BACK.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=10,
        description="Pull bar to upper chest, lean back slightly, squeeze lats at bottom.",
    ),
    ExerciseTemplate(
        "Seated Cable Row", MuscleGroup.BACK.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=12,
        description="Sit upright, pull handle to abdomen, squeeze shoulder blades together.",
    ),
    ExerciseTemplate(
        "Resistance Band Row", MuscleGroup.BACK.value, "strength",
        Equipment.RESISTANCE_BAND.value,
        [WorkoutType.HOME.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=15,
        description="Anchor band at waist height, pull elbows back and squeeze shoulder blades.",
    ),

    # ── SHOULDERS ────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Barbell Overhead Press", MuscleGroup.SHOULDERS.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=6,
        description="Press bar overhead from front rack, lock out arms, lower under control.",
    ),
    ExerciseTemplate(
        "Dumbbell Lateral Raise", MuscleGroup.SHOULDERS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Slight bend in elbows, raise arms to shoulder height, lower slowly.",
    ),
    ExerciseTemplate(
        "Dumbbell Shoulder Press", MuscleGroup.SHOULDERS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=10,
        description="Press dumbbells from ear height to overhead, avoid arching lower back.",
    ),
    ExerciseTemplate(
        "Face Pull", MuscleGroup.SHOULDERS.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Pull rope to forehead level, flare elbows out, squeeze rear delts.",
    ),
    ExerciseTemplate(
        "Pike Push-Up", MuscleGroup.SHOULDERS.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=10,
        description="Hips high in pike position, lower head between hands, press back up.",
    ),

    # ── BICEPS ───────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Barbell Curl", MuscleGroup.BICEPS.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Keep elbows fixed at sides, curl bar to shoulders, lower with control.",
    ),
    ExerciseTemplate(
        "Dumbbell Hammer Curl", MuscleGroup.BICEPS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Neutral grip (thumbs up), curl to shoulder height, squeeze at top.",
    ),
    ExerciseTemplate(
        "Cable Curl", MuscleGroup.BICEPS.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Constant cable tension throughout movement. Keep elbows stationary.",
    ),
    ExerciseTemplate(
        "Resistance Band Curl", MuscleGroup.BICEPS.value, "strength",
        Equipment.RESISTANCE_BAND.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=15,
        description="Stand on band, curl up to shoulder height, squeeze at the top.",
    ),

    # ── TRICEPS ──────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Triceps Dip", MuscleGroup.TRICEPS.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Lower body between hands on a bench or chair, push back up.",
    ),
    ExerciseTemplate(
        "Cable Triceps Pushdown", MuscleGroup.TRICEPS.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Keep elbows tucked at sides, push bar down to full extension.",
    ),
    ExerciseTemplate(
        "Skull Crusher", MuscleGroup.TRICEPS.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=10,
        description="Lower bar toward forehead by hinging at elbows only. Press back up.",
    ),
    ExerciseTemplate(
        "Dumbbell Overhead Triceps Extension", MuscleGroup.TRICEPS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Hold one dumbbell overhead with both hands, lower behind head, extend back up.",
    ),

    # ── LEGS ─────────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Barbell Back Squat", MuscleGroup.LEGS.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=8,
        description="Bar on upper traps, squat to parallel, drive through heels to stand.",
    ),
    ExerciseTemplate(
        "Goblet Squat", MuscleGroup.LEGS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=12,
        description="Hold dumbbell at chest, feet shoulder-width, squat deep, elbows inside knees.",
    ),
    ExerciseTemplate(
        "Bodyweight Squat", MuscleGroup.LEGS.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.FULL_BODY.value, WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=20,
        description="Feet shoulder-width, chest up, squat until thighs parallel, stand tall.",
    ),
    ExerciseTemplate(
        "Leg Press", MuscleGroup.LEGS.value, "strength",
        Equipment.MACHINE.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=12,
        description="Feet mid-platform, press to near-full extension, lower under control.",
    ),
    ExerciseTemplate(
        "Romanian Deadlift", MuscleGroup.LEGS.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=10,
        description="Hinge at hips, soft knee bend, lower bar along shins, feel hamstring stretch.",
    ),
    ExerciseTemplate(
        "Dumbbell Lunge", MuscleGroup.LEGS.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Step forward, lower back knee toward floor, push front foot to return.",
    ),
    ExerciseTemplate(
        "Bodyweight Lunge", MuscleGroup.LEGS.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=12,
        description="Alternate legs. Keep torso upright, front shin vertical at bottom.",
    ),
    ExerciseTemplate(
        "Leg Curl Machine", MuscleGroup.LEGS.value, "strength",
        Equipment.MACHINE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Curl heels toward glutes, pause at top, lower slowly.",
    ),
    ExerciseTemplate(
        "Kettlebell Swing", MuscleGroup.LEGS.value, "strength",
        Equipment.KETTLEBELL.value,
        [WorkoutType.FULL_BODY.value, WorkoutType.HOME.value, WorkoutType.CARDIO.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=15,
        description="Hip hinge power, not a squat. Drive hips forward, let arms swing to shoulder height.",
    ),

    # ── GLUTES ───────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Hip Thrust", MuscleGroup.GLUTES.value, "strength",
        Equipment.BARBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=4, default_reps=10,
        description="Upper back on bench, bar across hips, drive hips to full extension, squeeze glutes.",
    ),
    ExerciseTemplate(
        "Dumbbell Hip Thrust", MuscleGroup.GLUTES.value, "strength",
        Equipment.DUMBBELL.value,
        [WorkoutType.SPLIT.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default_sets=3, default_reps=15,
        description="Place dumbbell on hips, drive up and squeeze glutes hard at top.",
    ),
    ExerciseTemplate(
        "Glute Bridge", MuscleGroup.GLUTES.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=20,
        description="Lie on back, feet flat, push hips up and squeeze glutes at top.",
    ),
    ExerciseTemplate(
        "Cable Kickback", MuscleGroup.GLUTES.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Attach ankle cuff, hinge forward slightly, kick leg back and squeeze glute.",
    ),

    # ── CORE ─────────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Plank", MuscleGroup.CORE.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value, WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=1,
        description="Hold position for 30–60 seconds. Keep hips level, brace core.",
    ),
    ExerciseTemplate(
        "Hanging Leg Raise", MuscleGroup.CORE.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.SPLIT.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=12,
        description="Hang from bar, raise legs to hip height or higher, lower with control.",
    ),
    ExerciseTemplate(
        "Cable Crunch", MuscleGroup.CORE.value, "strength",
        Equipment.CABLE.value,
        [WorkoutType.SPLIT.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=15,
        description="Kneel, hold rope at head, crunch elbows toward knees, control return.",
    ),
    ExerciseTemplate(
        "Ab Wheel Rollout", MuscleGroup.CORE.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.SPLIT.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=10,
        description="Roll out slowly, brace core hard, pull back with lats and abs.",
    ),
    ExerciseTemplate(
        "Mountain Climber", MuscleGroup.CORE.value, "strength",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.HOME.value, WorkoutType.FULL_BODY.value, WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_sets=3, default_reps=20,
        description="Plank position, alternate driving knees to chest, keep hips down.",
    ),

    # ── CARDIO ───────────────────────────────────────────────────────────
    ExerciseTemplate(
        "Treadmill Run", MuscleGroup.CARDIO.value, "cardio",
        Equipment.CARDIO_MACHINE.value,
        [WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=30.0,
        description="Moderate pace (zone 2). Conversational breathing throughout.",
    ),
    ExerciseTemplate(
        "Stationary Bike", MuscleGroup.CARDIO.value, "cardio",
        Equipment.CARDIO_MACHINE.value,
        [WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=25.0,
        description="Steady effort, moderate resistance. Focus on consistent cadence.",
    ),
    ExerciseTemplate(
        "Jump Rope", MuscleGroup.CARDIO.value, "cardio",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.CARDIO.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=15.0,
        description="Basic bounce or alternating feet. Wrists do the work, not arms.",
    ),
    ExerciseTemplate(
        "Burpee", MuscleGroup.FULL_BODY.value, "cardio",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.CARDIO.value, WorkoutType.HOME.value, WorkoutType.FULL_BODY.value],
        [FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=10.0,
        description="Squat, kick back to plank, push-up, jump feet in, jump up. Full body explosive.",
    ),
    ExerciseTemplate(
        "Rowing Machine", MuscleGroup.FULL_BODY.value, "cardio",
        Equipment.CARDIO_MACHINE.value,
        [WorkoutType.CARDIO.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=20.0,
        description="Legs, core, arms in that order on the drive. Ratio: 1 part drive, 2 parts recovery.",
    ),
    ExerciseTemplate(
        "High Knees", MuscleGroup.CARDIO.value, "cardio",
        Equipment.BODYWEIGHT.value,
        [WorkoutType.CARDIO.value, WorkoutType.HOME.value],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value, FitnessLevel.ADVANCED.value],
        default_duration_min=10.0,
        description="Drive knees to hip height alternately. Stay on balls of feet.",
    ),
]


# ---------------------------------------------------------------------------
# WorkoutTemplate — generated workout plan
# ---------------------------------------------------------------------------

class WorkoutTemplate:
    """A generated workout plan tailored to a specific UserProfile.

    Produced by WorkoutGenerator — not stored directly, but can be converted
    to a WorkoutSession when the user actually completes it.

    Args:
        workout_type:  The type of workout (e.g. 'full_body', 'split').
        user_id:       The id of the UserProfile this was generated for.
        exercises:     List of ExerciseTemplate objects in this plan.
    """

    def __init__(
        self,
        workout_type: str,
        user_id: str,
        exercises: list[ExerciseTemplate],
    ) -> None:
        self._workout_type = workout_type
        self._user_id      = user_id
        self._exercises    = exercises

    @property
    def workout_type(self) -> str:
        return self._workout_type

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def exercises(self) -> list[ExerciseTemplate]:
        return list(self._exercises)

    def exercise_count(self) -> int:
        return len(self._exercises)

    def to_dict(self) -> dict:
        return {
            "workout_type": self._workout_type,
            "user_id":      self._user_id,
            "exercises":    [ex.to_dict() for ex in self._exercises],
        }

    def __repr__(self) -> str:
        return (
            f"WorkoutTemplate(type={self._workout_type!r}, "
            f"exercises={len(self._exercises)})"
        )


# ---------------------------------------------------------------------------
# WorkoutGenerator — polymorphic workout generation
# ---------------------------------------------------------------------------

class WorkoutGenerator:
    """Generates a WorkoutTemplate tailored to a UserProfile.

    Uses the EXERCISE_DATABASE and filters by workout_type, level,
    and available equipment. Applies goal-based adjustments to
    sets/reps recommendations.

    The generation strategy differs per workout type — demonstrating
    polymorphism through type-dispatch:
        - FULL_BODY: balanced selection across all muscle groups
        - SPLIT:     focused selection on target muscle group(s)
        - HOME:      bodyweight + limited equipment only
        - CARDIO:    cardio exercises with duration scaled to level
    """

    # How many exercises to include per workout type
    _EXERCISE_COUNTS: dict[str, int] = {
        WorkoutType.FULL_BODY.value: 8,
        WorkoutType.SPLIT.value:    6,
        WorkoutType.HOME.value:     7,
        WorkoutType.CARDIO.value:   4,
    }

    # Goal → (sets_modifier, reps_modifier) multipliers
    _GOAL_MODIFIERS: dict[str, tuple[float, float]] = {
        FitnessGoal.STRENGTH.value:    (1.3, 0.7),   # more sets, fewer reps
        FitnessGoal.MUSCLE_GAIN.value: (1.0, 1.0),   # default
        FitnessGoal.WEIGHT_LOSS.value: (0.9, 1.3),   # fewer sets, more reps
        FitnessGoal.ENDURANCE.value:   (0.8, 1.5),   # circuit-style
    }

    def __init__(self, database: list[ExerciseTemplate] | None = None) -> None:
        self._db = database if database is not None else EXERCISE_DATABASE

    def generate(
        self,
        profile: UserProfile,
        workout_type: str,
        focus_muscles: list[str] | None = None,
    ) -> WorkoutTemplate:
        """Generate a WorkoutTemplate tailored to the profile body stats and goal.

        BMI influences workout composition:
          - underweight → prioritise strength, reduce cardio
          - normal      → balanced selection
          - overweight  → boost cardio share
          - obese       → maximise cardio and low-impact movements
        """
        try:
            WorkoutType(workout_type)
        except ValueError:
            raise ValueError(
                f"Invalid workout_type '{workout_type}'. Choose: "
                + ", ".join(w.value for w in WorkoutType)
            )

        user_equipment = profile.equipment + [Equipment.BODYWEIGHT.value]
        bmi_cat        = profile.bmi_category()

        candidates = [
            ex for ex in self._db
            if ex.fits(workout_type, profile.level, user_equipment)
        ]

        if workout_type == WorkoutType.SPLIT.value and focus_muscles:
            focused = [ex for ex in candidates if ex.muscle_group in focus_muscles]
            candidates = focused if focused else candidates

        # BMI-based reordering
        if bmi_cat in ("overweight", "obese") and workout_type != WorkoutType.CARDIO.value:
            cardio_ex   = [ex for ex in candidates if ex.exercise_type == "cardio"]
            strength_ex = [ex for ex in candidates if ex.exercise_type == "strength"]
            candidates  = cardio_ex + strength_ex
        elif bmi_cat == "underweight":
            strength_ex = [ex for ex in candidates if ex.exercise_type == "strength"]
            cardio_ex   = [ex for ex in candidates if ex.exercise_type == "cardio"]
            candidates  = strength_ex + cardio_ex

        target_count = self._EXERCISE_COUNTS.get(workout_type, 6)
        if bmi_cat in ("overweight", "obese") and workout_type != WorkoutType.CARDIO.value:
            target_count = min(target_count + 1, 10)

        selected = self._select(candidates, workout_type, target_count)
        adjusted = self._apply_goal(selected, profile.goal, bmi_cat)

        return WorkoutTemplate(
            workout_type=workout_type,
            user_id=profile.id,
            exercises=adjusted,
        )

    def _select(
        self,
        candidates: list[ExerciseTemplate],
        workout_type: str,
        target: int,
    ) -> list[ExerciseTemplate]:
        """Select a balanced set of exercises from candidates."""
        if workout_type == WorkoutType.FULL_BODY.value:
            return self._balanced_select(candidates, target)
        if workout_type == WorkoutType.CARDIO.value:
            cardio = [ex for ex in candidates if ex.exercise_type == "cardio"]
            return cardio[:target] if cardio else candidates[:target]
        return candidates[:target]

    def _balanced_select(
        self,
        candidates: list[ExerciseTemplate],
        target: int,
    ) -> list[ExerciseTemplate]:
        """Select exercises covering diverse muscle groups."""
        by_muscle: dict[str, list[ExerciseTemplate]] = {}
        for ex in candidates:
            by_muscle.setdefault(ex.muscle_group, []).append(ex)

        selected: list[ExerciseTemplate] = []
        groups   = list(by_muscle.keys())
        i        = 0
        while len(selected) < target and i < target * 3:
            group = groups[i % len(groups)]
            pool  = by_muscle[group]
            if pool:
                selected.append(pool.pop(0))
            i += 1

        return selected[:target]

    def _apply_goal(
        self,
        exercises: list[ExerciseTemplate],
        goal: str,
        bmi_cat: Optional[str] = None,
    ) -> list[ExerciseTemplate]:
        """Return copies of templates with sets/reps adjusted for goal and BMI."""
        import copy
        sets_mod, reps_mod = self._GOAL_MODIFIERS.get(goal, (1.0, 1.0))
        # BMI adjustments on top of goal modifiers
        if bmi_cat == "underweight":
            sets_mod *= 1.1   # slightly more sets for muscle gain
            reps_mod *= 0.9
        elif bmi_cat in ("overweight", "obese"):
            reps_mod *= 1.15  # more reps for calorie burn
        adjusted = []
        for ex in exercises:
            t = copy.copy(ex)
            if ex.exercise_type == "strength":
                t.default_sets = max(1, round(ex.default_sets * sets_mod))
                t.default_reps = max(1, round(ex.default_reps * reps_mod))
            adjusted.append(t)
        return adjusted


# ---------------------------------------------------------------------------
# WorkoutSession
# ---------------------------------------------------------------------------

class WorkoutSession:
    """A single logged training session containing exercises.

    Args:
        session_date:  Date of the session (YYYY-MM-DD, defaults to today).
        label:         Optional label, e.g. 'Push Day'.
        workout_type:  WorkoutType enum value, defaults to 'full_body'.
        user_id:       Optional reference to the UserProfile.
        _id:           Internal — used when reconstructing from JSON.
    """

    def __init__(
        self,
        session_date: Optional[str] = None,
        label: str = "",
        workout_type: str = WorkoutType.FULL_BODY.value,
        user_id: Optional[str] = None,
        _id: Optional[str] = None,
    ) -> None:
        self._id          = _id if _id else str(uuid.uuid4())
        self.session_date = session_date or date.today().isoformat()
        self.label        = label
        self.workout_type = workout_type
        self.user_id      = user_id
        self._exercises: dict[str, Exercise] = {}

    @property
    def id(self) -> str:
        return self._id

    @property
    def session_date(self) -> str:
        return self._session_date

    @session_date.setter
    def session_date(self, value: str) -> None:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("session_date must be in YYYY-MM-DD format.")
        self._session_date = value

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = value.strip()

    @property
    def workout_type(self) -> str:
        return self._workout_type

    @workout_type.setter
    def workout_type(self, value: str) -> None:
        try:
            self._workout_type = WorkoutType(value).value
        except ValueError:
            self._workout_type = WorkoutType.FULL_BODY.value

    def add_exercise(self, exercise: Exercise) -> Exercise:
        self._exercises[exercise.id] = exercise
        return exercise

    def remove_exercise(self, exercise_id: str) -> bool:
        if exercise_id in self._exercises:
            del self._exercises[exercise_id]
            return True
        return False

    def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        return self._exercises.get(exercise_id)

    def get_all_exercises(self) -> list[Exercise]:
        return list(self._exercises.values())

    def exercise_count(self) -> int:
        return len(self._exercises)

    def total_volume(self) -> float:
        return sum(
            ex.total_volume()
            for ex in self._exercises.values()
            if isinstance(ex, StrengthExercise)
        )

    def total_cardio_minutes(self) -> float:
        return sum(
            ex.duration_min
            for ex in self._exercises.values()
            if isinstance(ex, CardioExercise)
        )

    def to_dict(self) -> dict:
        return {
            "id":           self._id,
            "session_date": self._session_date,
            "label":        self._label,
            "workout_type": self._workout_type,
            "user_id":      self.user_id,
            "exercises":    [ex.to_dict() for ex in self._exercises.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkoutSession":
        session = cls(
            session_date=data.get("session_date"),
            label=data.get("label", ""),
            workout_type=data.get("workout_type", WorkoutType.FULL_BODY.value),
            user_id=data.get("user_id"),
            _id=data.get("id"),
        )
        for ex_data in data.get("exercises", []):
            session.add_exercise(exercise_from_dict(ex_data))
        return session

    def __contains__(self, exercise_id: str) -> bool:
        return exercise_id in self._exercises

    def __repr__(self) -> str:
        return (
            f"WorkoutSession(id={self._id!r}, date={self._session_date!r}, "
            f"type={self._workout_type!r}, exercises={len(self._exercises)})"
        )


# ---------------------------------------------------------------------------
# WorkoutLog — main CRUD container
# ---------------------------------------------------------------------------

class WorkoutLog:
    """Persistent store for all workout sessions and user profiles.

    Stores sessions and profiles in dicts keyed by UUID for O(1) lookup.
    Serialises to / deserialises from a JSON file.

    Args:
        data_file: Path to the JSON persistence file.
    """

    def __init__(self, data_file: str = "workouts.json") -> None:
        self._data_file = data_file
        self._sessions: dict[str, WorkoutSession] = {}
        self._profiles: dict[str, UserProfile]    = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    raw: dict = json.load(f)
                for item in raw.get("sessions", []):
                    s = WorkoutSession.from_dict(item)
                    self._sessions[s.id] = s
                for item in raw.get("profiles", []):
                    p = UserProfile.from_dict(item)
                    self._profiles[p.id] = p
            except (json.JSONDecodeError, KeyError):
                self._sessions = {}
                self._profiles = {}

    def _save(self) -> None:
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "sessions": [s.to_dict() for s in self._sessions.values()],
                    "profiles": [p.to_dict() for p in self._profiles.values()],
                },
                f,
                indent=2,
            )

    # --- Profile CRUD ---

    def add_profile(self, profile: UserProfile) -> UserProfile:
        self._profiles[profile.id] = profile
        self._save()
        return profile

    def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        return self._profiles.get(profile_id)

    def get_all_profiles(self) -> list[UserProfile]:
        return list(self._profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._save()
            return True
        return False

    def update_profile(self, profile_id: str, **kwargs) -> Optional[UserProfile]:
        profile = self._profiles.get(profile_id)
        if profile is None:
            return None
        for key, value in kwargs.items():
            if hasattr(profile, key) and key != "id":
                setattr(profile, key, value)
        self._save()
        return profile

    # --- Session CRUD ---

    def add_session(self, session: WorkoutSession) -> WorkoutSession:
        self._sessions[session.id] = session
        self._save()
        return session

    def get_session(self, session_id: str) -> Optional[WorkoutSession]:
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> list[WorkoutSession]:
        return sorted(
            self._sessions.values(),
            key=lambda s: s.session_date,
            reverse=True,
        )

    def get_sessions_by_user(self, user_id: str) -> list[WorkoutSession]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()
            return True
        return False

    def update_session(self, session_id: str, **kwargs) -> Optional[WorkoutSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key) and key != "id":
                setattr(session, key, value)
        self._save()
        return session

    # --- Exercise CRUD inside session ---

    def add_exercise_to_session(
        self, session_id: str, exercise: Exercise
    ) -> Optional[Exercise]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        session.add_exercise(exercise)
        self._save()
        return exercise

    def remove_exercise_from_session(
        self, session_id: str, exercise_id: str
    ) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        removed = session.remove_exercise(exercise_id)
        if removed:
            self._save()
        return removed

    # --- Search ---

    def search(self, query: str) -> list[WorkoutSession]:
        q = query.lower().strip()
        results = []
        for session in self._sessions.values():
            if q in session.label.lower():
                results.append(session)
                continue
            for ex in session.get_all_exercises():
                if q in ex.name.lower() or q in ex.muscle_group.lower():
                    results.append(session)
                    break
        return sorted(results, key=lambda s: s.session_date, reverse=True)

    # --- Stats ---

    def total_sessions(self) -> int:
        return len(self._sessions)

    def personal_best(self, exercise_name: str) -> Optional[float]:
        best: Optional[float] = None
        name_lower = exercise_name.lower()
        for session in self._sessions.values():
            for ex in session.get_all_exercises():
                if (
                    isinstance(ex, StrengthExercise)
                    and ex.name.lower() == name_lower
                ):
                    if best is None or ex.weight_kg > best:
                        best = ex.weight_kg
        return best

    def __contains__(self, session_id: str) -> bool:
        return session_id in self._sessions

    def __len__(self) -> int:
        return len(self._sessions)
