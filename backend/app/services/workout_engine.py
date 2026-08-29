"""
Workout Engine Service — Exercise Database, Plan Generation & Tracking

Features:
- 87+ exercise database with muscle groups, difficulty, equipment, instructions
- Personalized workout plan generation (based on goals, fitness level, equipment)
- Active workout tracking (sets, reps, weight, RPE, rest timer)
- Workout history and analytics
- Personal record (PR) tracking
- Progressive overload suggestions
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class MuscleGroup(Enum):
    CHEST = "chest"; BACK = "back"; SHOULDERS = "shoulders"; BICEPS = "biceps"
    TRICEPS = "triceps"; QUADS = "quads"; HAMSTRINGS = "hamstrings"; GLUTES = "glutes"
    CALVES = "calves"; CORE = "core"; FOREARMS = "forearms"; FULL_BODY = "full_body"


class Difficulty(Enum):
    BEGINNER = "beginner"; INTERMEDIATE = "intermediate"; ADVANCED = "advanced"


class ExerciseType(Enum):
    COMPOUND = "compound"; ISOLATION = "isolation"; CARDIO = "cardio"; STRETCHING = "stretching"


class Equipment(Enum):
    BARBELL = "barbell"; DUMBBELL = "dumbbell"; MACHINE = "machine"; CABLE = "cable"
    BODYWEIGHT = "bodyweight"; KETTLEBELL = "kettlebell"; RESISTANCE_BAND = "band"; NONE = "none"


@dataclass
class Exercise:
    id: str; name: str; muscle_groups: list[str]; difficulty: str; equipment: str
    exercise_type: str; instructions: str; tips: str; calories_per_min: float = 5.0
    video_url: str = ""; gif_url: str = ""


@dataclass
class WorkoutPlan:
    id: str; name: str; description: str; difficulty: str; duration_minutes: int
    exercises: list[dict]; target_muscles: list[str]; goal: str


@dataclass
class WorkoutSession:
    id: str; plan_id: str; start_time: float; end_time: Optional[float] = None
    exercises: list[dict] = field(default_factory=list); total_volume: float = 0
    total_calories: int = 0; duration_minutes: int = 0


class WorkoutEngineService:
    """Comprehensive workout engine with exercise database and plan generation."""

    def __init__(self):
        self._exercises = self._init_exercises()
        self._plans = self._init_plans()
        self._sessions: list[WorkoutSession] = []
        self._prs: dict[str, dict] = {}

    def get_exercises(self, muscle_group: Optional[str] = None, difficulty: Optional[str] = None,
                      equipment: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict:
        filtered = self._exercises
        if muscle_group: filtered = [e for e in filtered if muscle_group.lower() in e.muscle_groups]
        if difficulty: filtered = [e for e in filtered if e.difficulty == difficulty]
        if equipment: filtered = [e for e in filtered if e.equipment == equipment]
        start = (page - 1) * page_size
        return {"exercises": [{"id": e.id, "name": e.name, "muscle_groups": e.muscle_groups, "difficulty": e.difficulty, "equipment": e.equipment, "type": e.exercise_type, "instructions": e.instructions, "tips": e.tips, "calories_per_min": e.calories_per_min} for e in filtered[start:start + page_size]], "total": len(filtered), "page": page}

    def get_exercise(self, exercise_id: str) -> Optional[dict]:
        e = next((ex for ex in self._exercises if ex.id == exercise_id), None)
        if not e: return None
        return {"id": e.id, "name": e.name, "muscle_groups": e.muscle_groups, "difficulty": e.difficulty, "equipment": e.equipment, "type": e.exercise_type, "instructions": e.instructions, "tips": e.tips, "calories_per_min": e.calories_per_min, "video_url": e.video_url, "gif_url": e.gif_url}

    def generate_workout_plan(self, goal: str, fitness_level: str, available_equipment: list[str], duration_minutes: int = 45, days_per_week: int = 3) -> dict:
        suitable = [e for e in self._exercises if e.difficulty in (fitness_level, "beginner" if fitness_level == "beginner" else "intermediate")]
        if available_equipment: suitable = [e for e in suitable if e.equipment in available_equipment or e.equipment in ("bodyweight", "none")]
        plan_exercises = []
        if goal in ("muscle_gain", "strength"):
            muscle_split = [["chest", "triceps"], ["back", "biceps"], ["quads", "glutes", "core"], ["shoulders", "forearms"]]
            for day_muscles in muscle_split[:min(days_per_week, 4)]:
                day_exs = [e for e in suitable if any(m in e.muscle_groups for m in day_muscles)][:4]
                plan_exercises.append({"day": f"Day {len(plan_exercises) + 1}", "focus": ", ".join(day_muscles), "exercises": [{"name": e.name, "sets": 4 if e.exercise_type == "compound" else 3, "reps": "8-12" if goal == "muscle_gain" else "4-6", "rest_seconds": 90 if e.exercise_type == "compound" else 60} for e in day_exs]})
        else:
            day_exs = suitable[:6]
            plan_exercises.append({"day": "Full Body", "focus": "cardio + strength", "exercises": [{"name": e.name, "sets": 3, "reps": "12-15", "rest_seconds": 45} for e in day_exs]})
        return {"plan_name": f"{goal.replace('_', ' ').title()} Plan", "goal": goal, "level": fitness_level, "duration_minutes": duration_minutes, "days_per_week": days_per_week, "weekly_structure": plan_exercises, "exercises_count": sum(len(d["exercises"]) for d in plan_exercises)}

    def start_session(self, plan_id: str = "custom") -> dict:
        session = WorkoutSession(id=f"ws_{int(time.time())}", plan_id=plan_id, start_time=time.time())
        self._sessions.append(session)
        return {"session_id": session.id, "status": "active", "start_time": time.strftime("%H:%M")}

    def log_set(self, session_id: str, exercise_name: str, set_num: int, reps: int, weight: float = 0, rpe: int = 5) -> dict:
        for s in self._sessions:
            if s.id == session_id:
                s.exercises.append({"exercise": exercise_name, "set": set_num, "reps": reps, "weight": weight, "rpe": rpe, "timestamp": time.time()})
                volume = weight * reps
                s.total_volume += volume
                key = exercise_name.lower()
                if key not in self._prs or weight > self._prs[key]["weight"]:
                    self._prs[key] = {"weight": weight, "reps": reps, "date": time.strftime("%Y-%m-%d"), "is_new_pr": True}
                    return {"logged": True, "volume": volume, "new_pr": True, "pr_weight": weight}
                return {"logged": True, "volume": volume, "new_pr": False}
        return {"error": "Session not found"}

    def complete_session(self, session_id: str) -> dict:
        for s in self._sessions:
            if s.id == session_id:
                s.end_time = time.time()
                s.duration_minutes = int((s.end_time - s.start_time) / 60)
                s.total_calories = int(s.duration_minutes * 7)
                return {"completed": True, "duration_min": s.duration_minutes, "total_volume": s.total_volume, "total_calories": s.total_calories, "sets_completed": len(s.exercises)}
        return {"error": "Session not found"}

    def get_history(self, limit: int = 20) -> list[dict]:
        return [{"id": s.id, "date": time.strftime("%Y-%m-%d", time.localtime(s.start_time)), "duration": s.duration_minutes, "volume": s.total_volume, "calories": s.total_calories, "exercises": len(s.exercises)} for s in reversed(self._sessions[-limit:])]

    def get_prs(self) -> dict:
        return self._prs

    def get_workout_stats(self) -> dict:
        if not self._sessions: return {"total_workouts": 0}
        total_vol = sum(s.total_volume for s in self._sessions)
        total_cal = sum(s.total_calories for s in self._sessions)
        total_min = sum(s.duration_minutes for s in self._sessions)
        return {"total_workouts": len(self._sessions), "total_volume_kg": round(total_vol, 1), "total_calories": total_cal, "total_minutes": total_min, "avg_duration": round(total_min / len(self._sessions), 1), "pr_count": len(self._prs)}

    def get_plans(self) -> list[dict]:
        return [{"id": p.id, "name": p.name, "description": p.description, "difficulty": p.difficulty, "duration": p.duration_minutes, "exercises": len(p.exercises), "goal": p.goal} for p in self._plans]

    def _init_exercises(self) -> list[Exercise]:
        """Initialize 87 exercises across all muscle groups."""
        return [
            # === CHEST (8) ===
            Exercise("ex_001", "Barbell Bench Press", ["chest", "triceps", "shoulders"], "intermediate", "barbell", "compound", "Lie on bench, grip bar slightly wider than shoulders. Lower to chest, press up.", "Keep shoulder blades retracted. Feet flat on floor."),
            Exercise("ex_002", "Incline Dumbbell Press", ["chest", "shoulders"], "intermediate", "dumbbell", "compound", "Set bench to 30-45 degrees. Press dumbbells up from chest level.", "Don't lock elbows at top."),
            Exercise("ex_003", "Push-Up", ["chest", "triceps", "core"], "beginner", "bodyweight", "compound", "Hands shoulder-width apart. Lower body until chest nearly touches floor.", "Keep body in straight line. Engage core."),
            Exercise("ex_023", "Decline Bench Press", ["chest", "triceps"], "intermediate", "barbell", "compound", "Lie on decline bench. Lower bar to lower chest, press up.", "Use spotter. Focus on lower chest engagement."),
            Exercise("ex_024", "Chest Dip", ["chest", "triceps"], "intermediate", "bodyweight", "compound", "On parallel bars, lean forward and dip down, push up.", "Lean forward for chest focus. Keep elbows wide."),
            Exercise("ex_025", "Dumbbell Fly", ["chest"], "beginner", "dumbbell", "isolation", "Lie on flat bench, open arms wide, bring dumbbells together.", "Don't go too deep. Squeeze at the top."),
            Exercise("ex_022", "Cable Fly", ["chest"], "beginner", "cable", "isolation", "Set cables at chest height. Bring hands together in front.", "Maintain slight elbow bend. Squeeze chest at center."),
            Exercise("ex_026", "Pec Deck", ["chest"], "beginner", "machine", "isolation", "Sit in machine, bring handles together in front.", "Control the negative. Pause at center."),

            # === BACK (8) ===
            Exercise("ex_007", "Pull-Up", ["back", "biceps"], "intermediate", "bodyweight", "compound", "Hang from bar, pull up until chin over bar.", "Full range of motion. Avoid kipping."),
            Exercise("ex_008", "Barbell Row", ["back", "biceps"], "intermediate", "barbell", "compound", "Hinge forward, row bar to lower chest.", "Squeeze shoulder blades. Keep back flat."),
            Exercise("ex_027", "Lat Pulldown", ["back", "biceps"], "beginner", "cable", "compound", "Pull bar to upper chest, squeezing lats.", "Pull to chest not behind neck. Lean back slightly."),
            Exercise("ex_028", "Seated Cable Row", ["back"], "beginner", "cable", "compound", "Pull handle to lower chest, squeeze shoulder blades.", "Keep back straight. Don't use momentum."),
            Exercise("ex_029", "T-Bar Row", ["back", "biceps"], "intermediate", "barbell", "compound", "Straddle bar, row to chest with neutral grip.", "Keep chest against pad if available."),
            Exercise("ex_030", "Single-Arm Dumbbell Row", ["back", "biceps"], "beginner", "dumbbell", "compound", "Knee on bench, row dumbbell to hip.", "Pull to hip, not chest. Keep back flat."),
            Exercise("ex_031", "Straight-Arm Pulldown", ["back"], "beginner", "cable", "isolation", "Push bar down from chest height with straight arms.", "Engage lats throughout. Squeeze at bottom."),
            Exercise("ex_032", "Chin-Up", ["back", "biceps"], "intermediate", "bodyweight", "compound", "Underhand grip pull-up, chin over bar.", "Full range of motion. Avoid kipping."),

            # === SHOULDERS (7) ===
            Exercise("ex_006", "Overhead Press", ["shoulders", "triceps"], "intermediate", "barbell", "compound", "Press bar from shoulders overhead until arms locked.", "Brace core. Don't lean back excessively."),
            Exercise("ex_013", "Lateral Raise", ["shoulders"], "beginner", "dumbbell", "isolation", "Raise dumbbells to sides until arms parallel to floor.", "Slight bend in elbows. Control movement."),
            Exercise("ex_016", "Face Pull", ["shoulders", "back"], "beginner", "cable", "isolation", "Pull rope to face level, elbows high.", "Great for shoulder health."),
            Exercise("ex_034", "Cable Lateral Raise", ["shoulders"], "beginner", "cable", "isolation", "Side raise with cable for constant tension.", "Lean slightly away from cable. Control the movement."),
            Exercise("ex_036", "Arnold Press", ["shoulders", "triceps"], "intermediate", "dumbbell", "compound", "Sit on bench, press dumbbells with rotation from front to overhead.", "Rotate palms from facing you to facing forward."),
            Exercise("ex_037", "Upright Row", ["shoulders", "biceps"], "intermediate", "barbell", "compound", "Pull bar to chin level, elbows leading.", "Use wide grip to reduce impingement risk."),
            Exercise("ex_038", "Rear Delt Fly", ["shoulders", "back"], "beginner", "dumbbell", "isolation", "Bend forward, raise dumbbells to sides.", "Slight bend in elbows. Focus on rear delts."),

            # === BICEPS (5) ===
            Exercise("ex_009", "Bicep Curl", ["biceps"], "beginner", "dumbbell", "isolation", "Stand with dumbbells at sides. Curl up, squeeze at top.", "Don't swing body. Control the negative."),
            Exercise("ex_040", "Preacher Curl", ["biceps"], "beginner", "machine", "isolation", "Rest arm on preacher pad, curl weight up.", "No swinging. Squeeze at top."),
            Exercise("ex_041", "Concentration Curl", ["biceps"], "beginner", "dumbbell", "isolation", "Sit on bench, curl dumbbell with elbow on inner thigh.", "Full contraction at top. Slow negative."),
            Exercise("ex_042", "Cable Curl", ["biceps"], "beginner", "cable", "isolation", "Curl bar attached to low cable.", "Constant tension throughout. No momentum."),
            Exercise("ex_043", "Incline Dumbbell Curl", ["biceps"], "intermediate", "dumbbell", "isolation", "Sit on 45 degree incline bench, curl dumbbells.", "Full stretch at bottom. Great for long head."),

            # === TRICEPS (5) ===
            Exercise("ex_010", "Tricep Dip", ["triceps", "chest"], "intermediate", "bodyweight", "compound", "Lower body by bending elbows to 90 degrees, push back up.", "Keep elbows close to body for tricep focus."),
            Exercise("ex_045", "Skull Crushers", ["triceps"], "intermediate", "barbell", "isolation", "Lie on bench, lower bar to forehead, extend arms.", "Keep elbows stationary. Use EZ bar for wrist comfort."),
            Exercise("ex_046", "Tricep Pushdown", ["triceps"], "beginner", "cable", "isolation", "Push cable attachment down to full extension.", "Keep elbows locked at sides. Squeeze at bottom."),
            Exercise("ex_047", "Overhead Tricep Extension", ["triceps"], "beginner", "dumbbell", "isolation", "Hold dumbbell overhead, lower behind head, extend.", "Keep elbows close to head. Full stretch at bottom."),
            Exercise("ex_048", "Tricep Kickback", ["triceps"], "beginner", "dumbbell", "isolation", "Bend over, extend arm back until straight.", "Squeeze at full extension. Keep upper arm still."),

            # === LEGS - QUADS (8) ===
            Exercise("ex_004", "Barbell Back Squat", ["quads", "glutes", "core"], "intermediate", "barbell", "compound", "Bar on upper traps. Squat down until thighs parallel to floor.", "Drive through heels. Keep chest up."),
            Exercise("ex_012", "Leg Press", ["quads", "glutes"], "beginner", "machine", "compound", "Sit in machine, press platform away with feet.", "Don't lock knees fully."),
            Exercise("ex_015", "Lunges", ["quads", "glutes"], "beginner", "bodyweight", "compound", "Step forward, lower back knee toward floor, push back up.", "Keep front knee over ankle."),
            Exercise("ex_050", "Goblet Squat", ["quads", "glutes"], "beginner", "dumbbell", "compound", "Hold dumbbell at chest, squat down.", "Great squat pattern learning tool. Elbows inside knees."),
            Exercise("ex_051", "Bulgarian Split Squat", ["quads", "glutes"], "intermediate", "dumbbell", "compound", "Rear foot on bench, squat on front leg.", "Keep torso upright. Great for imbalances."),
            Exercise("ex_052", "Hack Squat", ["quads", "glutes"], "intermediate", "machine", "compound", "In machine, squat deep with back supported.", "Place feet low on platform for more quad emphasis."),
            Exercise("ex_053", "Leg Extension", ["quads"], "beginner", "machine", "isolation", "Extend legs until straight, squeeze quads.", "Don't lock knees violently. Control the negative."),
            Exercise("ex_054", "Front Squat", ["quads", "core"], "advanced", "barbell", "compound", "Bar in front rack position, squat down.", "Keep elbows high. Torso stays very upright."),

            # === LEGS - HAMSTRINGS & GLUTES (6) ===
            Exercise("ex_005", "Deadlift", ["back", "glutes", "hamstrings"], "advanced", "barbell", "compound", "Stand with feet hip-width. Grip bar, hinge at hips, stand up.", "Neutral spine. Drive through floor."),
            Exercise("ex_011", "Romanian Deadlift", ["hamstrings", "glutes"], "intermediate", "barbell", "compound", "Hold bar at hip level. Hinge forward, lower bar along legs.", "Slight knee bend. Feel stretch in hamstrings."),
            Exercise("ex_017", "Hip Thrust", ["glutes", "hamstrings"], "intermediate", "barbell", "compound", "Upper back on bench. Drive hips up with bar on lap.", "Squeeze glutes at top."),
            Exercise("ex_057", "Leg Curl", ["hamstrings"], "beginner", "machine", "isolation", "Lie face-down, curl weight toward glutes.", "Squeeze hamstrings at peak. Control the negative."),
            Exercise("ex_058", "Nordic Hamstring Curl", ["hamstrings"], "advanced", "bodyweight", "isolation", "Kneel, partner holds ankles, lower body slowly.", "Elite hamstring exercise. Use assistance as needed."),
            Exercise("ex_059", "Glute Bridge", ["glutes", "hamstrings"], "beginner", "bodyweight", "compound", "Lie on back, drive hips up, squeeze glutes.", "Hold at top for 2 seconds. Great glute activation."),

            # === CALVES (3) ===
            Exercise("ex_018", "Calf Raise", ["calves"], "beginner", "machine", "isolation", "Stand on platform, raise heels, lower slowly.", "Full range of motion. Pause at top."),
            Exercise("ex_062", "Standing Calf Raise", ["calves"], "beginner", "machine", "isolation", "Raise heels on calf machine, full stretch at bottom.", "Hold at top for 1 second. Full range of motion."),
            Exercise("ex_063", "Single-Leg Calf Raise", ["calves"], "beginner", "bodyweight", "isolation", "Stand on one leg on edge of step, raise heel.", "Use wall for balance. Full stretch and contraction."),

            # === CORE (8) ===
            Exercise("ex_014", "Plank", ["core"], "beginner", "bodyweight", "isolation", "Hold body in straight line from head to heels.", "Breathe normally. Don't let hips sag."),
            Exercise("ex_019", "Mountain Climbers", ["core", "full_body"], "beginner", "bodyweight", "cardio", "In plank position, alternate driving knees to chest.", "Keep hips level. Move quickly."),
            Exercise("ex_065", "Dead Bug", ["core"], "beginner", "bodyweight", "isolation", "Lie on back, extend opposite arm and leg while maintaining flat back.", "Press lower back into floor throughout."),
            Exercise("ex_066", "Russian Twist", ["core"], "intermediate", "bodyweight", "isolation", "Sit with knees bent, lean back 45 degrees, rotate torso side to side.", "Keep feet off floor for difficulty."),
            Exercise("ex_067", "Hanging Leg Raise", ["core"], "intermediate", "bodyweight", "isolation", "Hang from bar, raise straight legs to 90 degrees.", "Control the movement. Avoid swinging."),
            Exercise("ex_068", "Ab Rollout", ["core"], "intermediate", "bodyweight", "isolation", "Kneel, roll wheel forward, pull back.", "Keep core tight throughout. Start with small range."),
            Exercise("ex_069", "Side Plank", ["core"], "beginner", "bodyweight", "isolation", "Lie on side, hold body in straight line.", "Great for obliques. Don't let hips drop."),
            Exercise("ex_070", "Bicycle Crunch", ["core"], "beginner", "bodyweight", "isolation", "Lie on back, alternate elbow to opposite knee.", "Full rotation. Don't pull on neck."),

            # === FOREARMS (2) ===
            Exercise("ex_073", "Wrist Curl", ["forearms"], "beginner", "dumbbell", "isolation", "Forearm on thigh, curl dumbbell with wrist.", "Full range of motion. Slow reps."),
            Exercise("ex_074", "Farmers Walk", ["forearms", "full_body"], "beginner", "dumbbell", "compound", "Hold heavy dumbbells, walk 30-50 meters.", "Great for grip strength and conditioning."),

            # === FULL BODY & COMPOUND (3) ===
            Exercise("ex_020", "Burpee", ["full_body"], "intermediate", "bodyweight", "cardio", "Drop to floor, do push-up, jump feet to hands, jump up.", "Scale by removing jump if needed."),
            Exercise("ex_071", "Turkish Get-Up", ["core", "full_body"], "advanced", "kettlebell", "compound", "From lying, stand up while holding weight overhead.", "Complex movement. Master with no weight first."),
            Exercise("ex_060", "Good Morning", ["hamstrings", "glutes", "core"], "intermediate", "barbell", "compound", "Bar on back, hinge at hips, lower torso.", "Keep slight knee bend. Don't go too heavy."),

            # === CARDIO (10) ===
            Exercise("ex_075", "Jump Rope", ["full_body"], "beginner", "bodyweight", "cardio", "Jump rope continuously for time.", "Stay on balls of feet. Great for coordination."),
            Exercise("ex_076", "High Knees", ["full_body", "core"], "beginner", "bodyweight", "cardio", "Run in place, driving knees to hip height.", "Pump arms. Land softly."),
            Exercise("ex_077", "Box Jump", ["quads", "glutes"], "intermediate", "bodyweight", "cardio", "Jump onto box, step down.", "Land softly with bent knees. Use appropriate height."),
            Exercise("ex_078", "Battle Ropes", ["full_body"], "intermediate", "bodyweight", "cardio", "Alternate slamming ropes up and down.", "Keep core tight. Vary wave patterns."),
            Exercise("ex_079", "Rowing Machine", ["back", "legs"], "beginner", "machine", "cardio", "Row with legs, lean back, pull handle to chest.", "Drive with legs first. Great full-body cardio."),
            Exercise("ex_080", "Assault Bike", ["full_body"], "intermediate", "machine", "cardio", "Pedal and push and pull handles simultaneously.", "All-out effort for intervals. Great calorie burner."),
            Exercise("ex_081", "Sled Push", ["quads", "glutes"], "advanced", "machine", "cardio", "Push weighted sled across floor.", "Stay low. Drive through legs. Great conditioning."),
            Exercise("ex_082", "Stair Climber", ["quads", "glutes", "calves"], "beginner", "machine", "cardio", "Walk or climb on stair machine.", "Don't lean on rails. Great for lower body endurance."),
            Exercise("ex_039", "Machine Shoulder Press", ["shoulders", "triceps"], "beginner", "machine", "compound", "Sit and press handles overhead.", "Great for beginners. Full range of motion."),
            Exercise("ex_061", "Step-Up", ["quads", "glutes"], "beginner", "dumbbell", "compound", "Step onto box or bench, drive up, alternate legs.", "Use a challenging height. Drive through heel."),

            # === FLEXIBILITY & MOBILITY (5) ===
            Exercise("ex_083", "Downward Dog", ["hamstrings", "calves", "back"], "beginner", "bodyweight", "stretching", "Inverted V shape, press chest toward thighs.", "Pedal feet to stretch hamstrings alternately."),
            Exercise("ex_084", "Pigeon Pose", ["glutes"], "beginner", "bodyweight", "stretching", "Front leg bent on floor, back leg extended behind.", "Great for hip mobility. Hold 30-60 seconds."),
            Exercise("ex_085", "Worlds Greatest Stretch", ["full_body"], "beginner", "bodyweight", "stretching", "Lunge, rotate toward front knee, reach overhead.", "Combines hip flexor, thoracic, and hamstring stretch."),
            Exercise("ex_086", "Cat-Cow", ["back", "core"], "beginner", "bodyweight", "stretching", "On hands and knees, arch and round spine alternately.", "Breathe deeply. Move slowly through full range."),
            Exercise("ex_087", "Foam Roll IT Band", ["quads", "glutes"], "beginner", "bodyweight", "stretching", "Roll along outer thigh on foam roller.", "Pause on tender spots. Great for recovery."),

            # === BODYWEIGHT VARIATIONS (10) ===
            Exercise("ex_088", "Diamond Push-Up", ["chest", "triceps"], "intermediate", "bodyweight", "compound", "Hands together forming diamond shape, push-up.", "Great for inner chest and triceps."),
            Exercise("ex_089", "Pike Push-Up", ["shoulders", "triceps"], "intermediate", "bodyweight", "compound", "Inverted V position, lower head toward floor, press up.", "Begins handstand push-up progression."),
            Exercise("ex_090", "Archer Push-Up", ["chest", "shoulders"], "advanced", "bodyweight", "compound", "Wide hand placement, shift weight to one arm while lowering.", "One-arm push-up progression."),
            Exercise("ex_091", "Pistol Squat Prep", ["quads", "glutes"], "intermediate", "bodyweight", "compound", "Single-leg squat to bench, stand back up.", "Use bench for assistance. Progress depth over time."),
            Exercise("ex_092", "Hindu Push-Up", ["chest", "shoulders", "back"], "intermediate", "bodyweight", "compound", "From downward dog, swoop down and up into cobra.", "Fluid movement. Great for shoulder mobility."),
            Exercise("ex_093", "Wall Sit", ["quads", "glutes"], "beginner", "bodyweight", "isolation", "Back against wall, thighs parallel to floor, hold.", "Great isometric hold. Time yourself."),
            Exercise("ex_094", "Crab Walk", ["glutes", "hamstrings"], "beginner", "bodyweight", "compound", "Hands and feet on floor, walk forward and backward.", "Great for glute activation and coordination."),
            Exercise("ex_095", "Broad Jump", ["quads", "glutes"], "intermediate", "bodyweight", "cardio", "Standing long jump for maximum distance.", "Swing arms for momentum. Land softly."),
            Exercise("ex_096", "Lateral Lunge", ["quads", "glutes"], "beginner", "bodyweight", "compound", "Step to side, bend one knee, keep other leg straight.", "Great for inner thigh and lateral stability."),
            Exercise("ex_097", "Reverse Lunge", ["quads", "glutes"], "beginner", "bodyweight", "compound", "Step backward, lower knee toward floor, push back up.", "Easier on knees than forward lunges."),

            # === KETTLEBELL (5) ===
            Exercise("ex_098", "Kettlebell Swing", ["glutes", "hamstrings", "core"], "intermediate", "kettlebell", "compound", "Hinge at hips, swing bell between legs, thrust hips to swing up.", "Power comes from hips, not arms."),
            Exercise("ex_099", "Kettlebell Goblet Squat", ["quads", "glutes"], "beginner", "kettlebell", "compound", "Hold bell at chest, squat deep.", "Great for learning squat depth."),
            Exercise("ex_100", "Kettlebell Clean", ["back", "shoulders"], "intermediate", "kettlebell", "compound", "Pull bell from floor to rack position at shoulder.", "Smooth transition. Keep elbow tight."),
            Exercise("ex_101", "Kettlebell Snatch", ["shoulders", "back"], "advanced", "kettlebell", "compound", "Swing bell from between legs to overhead in one motion.", "Advanced power movement. Master swing first."),
            Exercise("ex_102", "Kettlebell Turkish Get-Up", ["core", "full_body"], "advanced", "kettlebell", "compound", "Lie down, stand up while holding bell overhead.", "Slow and controlled. 7 steps to master."),

            # === RESISTANCE BAND (4) ===
            Exercise("ex_103", "Band Pull-Apart", ["shoulders", "back"], "beginner", "band", "isolation", "Hold band at chest height, pull apart until arms extended.", "Great for rear delt and posture correction."),
            Exercise("ex_104", "Band Squat", ["quads", "glutes"], "beginner", "band", "compound", "Stand on band, hold handles at shoulders, squat.", "Accommodating resistance. Great for beginners."),
            Exercise("ex_105", "Band Bicep Curl", ["biceps"], "beginner", "band", "isolation", "Stand on band, curl handles up.", "Constant tension throughout range."),
            Exercise("ex_106", "Band Chest Press", ["chest", "triceps"], "beginner", "band", "compound", "Anchor band behind, press handles forward.", "Great for travel workouts."),

            # === YOGA & MOBILITY (5) ===
            Exercise("ex_107", "Warrior I", ["quads", "hip_flexors"], "beginner", "bodyweight", "stretching", "Lunge position, back foot at 45 degrees, arms overhead.", "Great hip flexor and quad stretch."),
            Exercise("ex_108", "Warrior II", ["quads", "hip_flexors"], "beginner", "bodyweight", "stretching", "Wide stance, front knee bent, arms extended to sides.", "Hold for 30 seconds each side."),
            Exercise("ex_109", "Childs Pose", ["back", "shoulders"], "beginner", "bodyweight", "stretching", "Kneel, sit back on heels, stretch arms forward on floor.", "Great recovery and relaxation pose."),
            Exercise("ex_110", "Seated Forward Fold", ["hamstrings", "back"], "beginner", "bodyweight", "stretching", "Sit with legs extended, fold forward from hips.", "Don't round back. Hinge from hips."),
            Exercise("ex_111", "Lizard Pose", ["hip_flexors", "glutes"], "intermediate", "bodyweight", "stretching", "Deep lunge with both hands inside front foot.", "Advanced hip opener. Ease into it."),
        ]

    def _init_plans(self) -> list[WorkoutPlan]:
        return [
            WorkoutPlan("plan_001", "Strength Foundation", "Build baseline strength with compound movements", "beginner", 45, [{"name": "Barbell Back Squat", "sets": 3, "reps": "10"}, {"name": "Bench Press", "sets": 3, "reps": "10"}, {"name": "Barbell Row", "sets": 3, "reps": "10"}, {"name": "Overhead Press", "sets": 3, "reps": "10"}], ["full_body"], "strength"),
            WorkoutPlan("plan_002", "Hypertrophy Split", "4-day upper/lower split for muscle growth", "intermediate", 60, [{"name": "Bench Press", "sets": 4, "reps": "8-12"}, {"name": "Incline Press", "sets": 3, "reps": "10-12"}, {"name": "Pull-Up", "sets": 4, "reps": "8-12"}, {"name": "Squat", "sets": 4, "reps": "8-12"}], ["full_body"], "muscle_gain"),
            WorkoutPlan("plan_003", "Fat Burner", "High-rep, minimal rest for calorie burn", "beginner", 30, [{"name": "Burpee", "sets": 3, "reps": "15"}, {"name": "Mountain Climber", "sets": 3, "reps": "30"}, {"name": "Lunge", "sets": 3, "reps": "20"}, {"name": "Plank", "sets": 3, "reps": "60s"}], ["full_body"], "weight_loss"),
            WorkoutPlan("plan_004", "5K Training Plan", "Progressive running plan for 5K races", "beginner", 40, [{"name": "Jump Rope", "sets": 1, "reps": "5 min warm-up"}, {"name": "Run/Walk Intervals", "sets": 1, "reps": "20 min"}, {"name": "Step-Up", "sets": 3, "reps": "12 each"}, {"name": "Plank", "sets": 3, "reps": "60s"}], ["legs", "core"], "cardio"),
            WorkoutPlan("plan_004b", "Push Pull Legs Split", "6-day PPL for advanced lifters", "advanced", 75, [{"name": "Bench Press", "sets": 5, "reps": "5"}, {"name": "Overhead Press", "sets": 4, "reps": "8"}, {"name": "Pull-Up", "sets": 4, "reps": "8"}, {"name": "Barbell Back Squat", "sets": 5, "reps": "5"}], ["full_body"], "strength"),
            WorkoutPlan("plan_005", "Flexibility & Mobility", "Daily stretching and mobility routine", "beginner", 20, [{"name": "Downward Dog", "sets": 1, "reps": "30s hold"}, {"name": "Pigeon Pose", "sets": 1, "reps": "30s each side"}, {"name": "Worlds Greatest Stretch", "sets": 1, "reps": "5 each side"}, {"name": "Cat-Cow", "sets": 1, "reps": "10 reps"}], ["full_body"], "flexibility"),
        ]


workout_engine_service = WorkoutEngineService()
