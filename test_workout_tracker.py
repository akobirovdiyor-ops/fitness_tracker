"""
test_workout_tracker.py
Pytest test suite — covers all classes in workout_tracker.py.
"""

import pytest

from workout_tracker import (
    CardioExercise,
    Equipment,
    ExerciseTemplate,
    FitnessGoal,
    FitnessLevel,
    MuscleGroup,
    StrengthExercise,
    UserProfile,
    WorkoutGenerator,
    WorkoutLog,
    WorkoutSession,
    WorkoutTemplate,
    WorkoutType,
    EXERCISE_DATABASE,
    exercise_from_dict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def strength():
    return StrengthExercise("Bench Press", "Chest", 4, 8, 80.0)


@pytest.fixture
def cardio():
    return CardioExercise("Treadmill Run", "Full Body", 30.0, 5.0)


@pytest.fixture
def session(strength, cardio):
    s = WorkoutSession(session_date="2025-06-01", label="Push Day", workout_type="split")
    s.add_exercise(strength)
    s.add_exercise(cardio)
    return s


@pytest.fixture
def empty_session():
    return WorkoutSession(session_date="2025-06-01", label="Empty", workout_type="full_body")


@pytest.fixture
def beginner_profile():
    return UserProfile(
        name="Alice",
        age=22,
        level="beginner",
        goal="weight_loss",
        equipment=["bodyweight", "dumbbell"],
        workout_days=3,
    )


@pytest.fixture
def advanced_profile():
    return UserProfile(
        name="Bob",
        age=30,
        level="advanced",
        goal="strength",
        equipment=["bodyweight", "barbell", "dumbbell", "cable", "machine"],
        workout_days=5,
    )


@pytest.fixture
def log(tmp_path, session, beginner_profile):
    wl = WorkoutLog(data_file=str(tmp_path / "test.json"))
    wl.add_profile(beginner_profile)
    session.user_id = beginner_profile.id
    wl.add_session(session)
    return wl


@pytest.fixture
def empty_log(tmp_path):
    return WorkoutLog(data_file=str(tmp_path / "empty.json"))


@pytest.fixture
def generator():
    return WorkoutGenerator()


# ---------------------------------------------------------------------------
# TestStrengthExercise
# ---------------------------------------------------------------------------

class TestStrengthExercise:
    def test_type(self, strength):
        assert strength.get_type() == "strength"

    def test_valid_creation(self, strength):
        assert strength.name == "Bench Press"
        assert strength.sets == 4
        assert strength.reps == 8
        assert strength.weight_kg == 80.0

    def test_name_stripped(self):
        ex = StrengthExercise("  Squat  ", "Legs", 3, 5, 100.0)
        assert ex.name == "Squat"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            StrengthExercise("", "Chest", 3, 8, 60.0)

    def test_empty_muscle_raises(self):
        with pytest.raises(ValueError, match="Muscle group cannot be empty"):
            StrengthExercise("Curl", "  ", 3, 10, 20.0)

    def test_sets_zero_raises(self):
        with pytest.raises(ValueError):
            StrengthExercise("Curl", "Biceps", 0, 10, 20.0)

    def test_reps_zero_raises(self):
        with pytest.raises(ValueError):
            StrengthExercise("Curl", "Biceps", 3, 0, 20.0)

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError):
            StrengthExercise("Curl", "Biceps", 3, 10, -5.0)

    def test_zero_weight_allowed(self):
        ex = StrengthExercise("Push-up", "Chest", 3, 15, 0.0)
        assert ex.weight_kg == 0.0

    def test_total_volume(self, strength):
        assert strength.total_volume() == 4 * 8 * 80.0

    def test_id_read_only(self, strength):
        with pytest.raises(AttributeError):
            strength.id = "new"

    def test_serialisation_contains_fields(self, strength):
        d = strength.to_dict()
        assert d["type"] == "strength"
        assert d["sets"] == 4
        assert "id" in d


# ---------------------------------------------------------------------------
# TestCardioExercise
# ---------------------------------------------------------------------------

class TestCardioExercise:
    def test_type(self, cardio):
        assert cardio.get_type() == "cardio"

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError):
            CardioExercise("Bike", "Full Body", 0)

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError):
            CardioExercise("Bike", "Full Body", 20, -1)

    def test_pace(self, cardio):
        assert cardio.pace_min_per_km() == 6.0

    def test_pace_zero_distance(self):
        ex = CardioExercise("Jump Rope", "Full Body", 15.0, 0.0)
        assert ex.pace_min_per_km() is None

    def test_serialisation(self, cardio):
        d = cardio.to_dict()
        assert d["type"] == "cardio"
        assert d["duration_min"] == 30.0


# ---------------------------------------------------------------------------
# TestExerciseIdentity
# ---------------------------------------------------------------------------

class TestExerciseIdentity:
    def test_unique_ids(self):
        a = StrengthExercise("OHP", "Shoulders", 3, 6, 50.0)
        b = StrengthExercise("OHP", "Shoulders", 3, 6, 50.0)
        assert a.id != b.id

    def test_round_trip_equality(self):
        ex = StrengthExercise("Deadlift", "Back", 3, 5, 120.0)
        assert ex == exercise_from_dict(ex.to_dict())


# ---------------------------------------------------------------------------
# TestUserProfile
# ---------------------------------------------------------------------------

class TestUserProfile:
    def test_valid_creation(self, beginner_profile):
        assert beginner_profile.name == "Alice"
        assert beginner_profile.level == "beginner"
        assert beginner_profile.goal == "weight_loss"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            UserProfile("", 25, "beginner", "strength", [])

    def test_age_too_low_raises(self):
        with pytest.raises(ValueError, match="Age must be between"):
            UserProfile("X", 10, "beginner", "strength", [])

    def test_age_too_high_raises(self):
        with pytest.raises(ValueError, match="Age must be between"):
            UserProfile("X", 110, "beginner", "strength", [])

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="Invalid level"):
            UserProfile("X", 25, "godmode", "strength", [])

    def test_invalid_goal_raises(self):
        with pytest.raises(ValueError, match="Invalid goal"):
            UserProfile("X", 25, "beginner", "fly_to_moon", [])

    def test_invalid_equipment_raises(self):
        with pytest.raises(ValueError, match="Invalid equipment"):
            UserProfile("X", 25, "beginner", "strength", ["magic_carpet"])

    def test_workout_days_out_of_range(self):
        with pytest.raises(ValueError, match="Workout days"):
            UserProfile("X", 25, "beginner", "strength", [], workout_days=8)

    def test_id_is_read_only(self, beginner_profile):
        with pytest.raises(AttributeError):
            beginner_profile.id = "new"

    def test_has_equipment(self, beginner_profile):
        assert beginner_profile.has_equipment("bodyweight") is True
        assert beginner_profile.has_equipment("barbell") is False

    def test_equipment_returns_copy(self, beginner_profile):
        eq = beginner_profile.equipment
        eq.append("barbell")
        assert "barbell" not in beginner_profile.equipment

    def test_serialisation_round_trip(self, beginner_profile):
        d = beginner_profile.to_dict()
        p2 = UserProfile.from_dict(d)
        assert p2.id == beginner_profile.id
        assert p2.name == beginner_profile.name
        assert p2.level == beginner_profile.level


# ---------------------------------------------------------------------------
# TestExerciseTemplate
# ---------------------------------------------------------------------------

class TestExerciseTemplate:
    def test_fits_matching(self):
        t = ExerciseTemplate(
            "Push-Up", "chest", "strength", "bodyweight",
            ["home", "full_body"], ["beginner", "intermediate"],
        )
        assert t.fits("home", "beginner", ["bodyweight"]) is True

    def test_fits_wrong_type(self):
        t = ExerciseTemplate(
            "Push-Up", "chest", "strength", "bodyweight",
            ["home"], ["beginner"],
        )
        assert t.fits("split", "beginner", ["bodyweight"]) is False

    def test_fits_missing_equipment(self):
        t = ExerciseTemplate(
            "Bench Press", "chest", "strength", "barbell",
            ["split"], ["intermediate"],
        )
        assert t.fits("split", "intermediate", ["bodyweight"]) is False

    def test_fits_wrong_level(self):
        t = ExerciseTemplate(
            "Muscle Up", "back", "strength", "bodyweight",
            ["split"], ["advanced"],
        )
        assert t.fits("split", "beginner", ["bodyweight"]) is False


# ---------------------------------------------------------------------------
# TestWorkoutGenerator
# ---------------------------------------------------------------------------

class TestWorkoutGenerator:
    def test_returns_workout_template(self, generator, beginner_profile):
        plan = generator.generate(beginner_profile, "home")
        assert isinstance(plan, WorkoutTemplate)

    def test_template_has_exercises(self, generator, beginner_profile):
        plan = generator.generate(beginner_profile, "home")
        assert plan.exercise_count() > 0

    def test_user_id_matches(self, generator, beginner_profile):
        plan = generator.generate(beginner_profile, "home")
        assert plan.user_id == beginner_profile.id

    def test_workout_type_matches(self, generator, beginner_profile):
        plan = generator.generate(beginner_profile, "home")
        assert plan.workout_type == "home"

    def test_invalid_workout_type_raises(self, generator, beginner_profile):
        with pytest.raises(ValueError, match="Invalid workout_type"):
            generator.generate(beginner_profile, "dance_party")

    def test_advanced_profile_gets_exercises(self, generator, advanced_profile):
        plan = generator.generate(advanced_profile, "full_body")
        assert plan.exercise_count() > 0

    def test_cardio_plan_has_cardio_exercises(self, generator, advanced_profile):
        plan = generator.generate(advanced_profile, "cardio")
        types = [ex.exercise_type for ex in plan.exercises]
        assert "cardio" in types

    def test_split_with_focus_muscles(self, generator, advanced_profile):
        plan = generator.generate(advanced_profile, "split", focus_muscles=["chest"])
        muscles = [ex.muscle_group for ex in plan.exercises]
        assert "chest" in muscles

    def test_goal_modifies_reps_for_endurance(self, generator):
        profile = UserProfile("Test", 25, "intermediate", "endurance", ["bodyweight", "dumbbell"])
        plan = generator.generate(profile, "full_body")
        strength_exs = [ex for ex in plan.exercises if ex.exercise_type == "strength"]
        if strength_exs:
            assert strength_exs[0].default_reps >= 10

    def test_goal_modifies_sets_for_strength(self, generator):
        profile = UserProfile("Test", 25, "advanced", "strength", ["bodyweight","barbell","dumbbell","cable","machine"])
        plan = generator.generate(profile, "split")
        strength_exs = [ex for ex in plan.exercises if ex.exercise_type == "strength"]
        if strength_exs:
            assert strength_exs[0].default_sets >= 3

    def test_template_serialisable(self, generator, beginner_profile):
        plan = generator.generate(beginner_profile, "home")
        d = plan.to_dict()
        assert "exercises" in d
        assert d["workout_type"] == "home"


# ---------------------------------------------------------------------------
# TestWorkoutSession
# ---------------------------------------------------------------------------

class TestWorkoutSession:
    def test_workout_type_stored(self):
        s = WorkoutSession(workout_type="cardio")
        assert s.workout_type == "cardio"

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            WorkoutSession(session_date="01-06-2025")

    def test_add_returns_exercise(self, empty_session, strength):
        assert empty_session.add_exercise(strength) is strength

    def test_contains(self, session, strength):
        assert strength.id in session

    def test_remove_returns_true(self, session, strength):
        assert session.remove_exercise(strength.id) is True

    def test_total_volume(self, session, strength):
        assert session.total_volume() == strength.total_volume()

    def test_total_cardio(self, session, cardio):
        assert session.total_cardio_minutes() == cardio.duration_min

    def test_round_trip(self, session):
        d = session.to_dict()
        s2 = WorkoutSession.from_dict(d)
        assert s2.id == session.id
        assert s2.workout_type == session.workout_type
        assert s2.exercise_count() == session.exercise_count()


# ---------------------------------------------------------------------------
# TestWorkoutLogProfiles
# ---------------------------------------------------------------------------

class TestWorkoutLogProfiles:
    def test_add_profile(self, empty_log, beginner_profile):
        empty_log.add_profile(beginner_profile)
        assert empty_log.get_profile(beginner_profile.id) is not None

    def test_get_all_profiles(self, log):
        assert len(log.get_all_profiles()) == 1

    def test_delete_profile(self, log, beginner_profile):
        assert log.delete_profile(beginner_profile.id) is True
        assert log.get_profile(beginner_profile.id) is None

    def test_delete_missing_returns_false(self, log):
        assert log.delete_profile("bad-id") is False

    def test_update_profile(self, log, beginner_profile):
        updated = log.update_profile(beginner_profile.id, name="Alicia")
        assert updated.name == "Alicia"

    def test_update_missing_returns_none(self, log):
        assert log.update_profile("bad-id", name="X") is None


# ---------------------------------------------------------------------------
# TestWorkoutLogSessions
# ---------------------------------------------------------------------------

class TestWorkoutLogSessions:
    def test_add_session(self, empty_log, session):
        empty_log.add_session(session)
        assert session.id in empty_log

    def test_get_session(self, log, session):
        assert log.get_session(session.id).id == session.id

    def test_get_sessions_by_user(self, log, session, beginner_profile):
        results = log.get_sessions_by_user(beginner_profile.id)
        assert any(s.id == session.id for s in results)

    def test_delete_session(self, log, session):
        assert log.delete_session(session.id) is True
        assert log.get_session(session.id) is None

    def test_search_by_label(self, log, session):
        results = log.search("Push")
        assert any(s.id == session.id for s in results)

    def test_search_no_match(self, log):
        assert log.search("zzz_no_match_zzz") == []

    def test_sorted_newest_first(self, empty_log):
        s1 = WorkoutSession(session_date="2025-01-01", label="Old")
        s2 = WorkoutSession(session_date="2025-12-01", label="New")
        empty_log.add_session(s1)
        empty_log.add_session(s2)
        assert empty_log.get_all_sessions()[0].session_date == "2025-12-01"

    def test_personal_best(self, log, session, strength):
        assert log.personal_best("Bench Press") == 80.0

    def test_personal_best_case_insensitive(self, log):
        assert log.personal_best("bench press") == 80.0


# ---------------------------------------------------------------------------
# TestPersistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_sessions_survive_reload(self, tmp_path, session):
        path = str(tmp_path / "persist.json")
        wl = WorkoutLog(data_file=path)
        wl.add_session(session)
        wl2 = WorkoutLog(data_file=path)
        assert session.id in wl2

    def test_profiles_survive_reload(self, tmp_path, beginner_profile):
        path = str(tmp_path / "persist.json")
        wl = WorkoutLog(data_file=path)
        wl.add_profile(beginner_profile)
        wl2 = WorkoutLog(data_file=path)
        assert wl2.get_profile(beginner_profile.id) is not None

    def test_empty_file_loads_cleanly(self, tmp_path):
        wl = WorkoutLog(data_file=str(tmp_path / "empty.json"))
        assert len(wl) == 0


# ---------------------------------------------------------------------------
# TestExerciseDatabase
# ---------------------------------------------------------------------------

class TestExerciseDatabase:
    def test_database_not_empty(self):
        assert len(EXERCISE_DATABASE) > 0

    def test_all_entries_are_templates(self):
        assert all(isinstance(ex, ExerciseTemplate) for ex in EXERCISE_DATABASE)

    def test_database_covers_all_workout_types(self):
        types_covered = {wt for ex in EXERCISE_DATABASE for wt in ex.workout_types}
        for wt in WorkoutType:
            assert wt.value in types_covered

    def test_database_covers_all_levels(self):
        levels_covered = {lv for ex in EXERCISE_DATABASE for lv in ex.levels}
        for lv in FitnessLevel:
            assert lv.value in levels_covered
