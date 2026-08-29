"""
Stroke Recovery & Neurological Rehabilitation Service
Neuroplasticity-based exercises, motor recovery, cognitive rehab, speech therapy
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random


class StrokeRehabService:
    """Stroke recovery and neurological rehabilitation platform"""

    def __init__(self):
        self.rehab_phases = {
            "acute": {
                "name": "Acute Phase",
                "duration_weeks": 4,
                "goals": ["Prevent complications", "Initiate mobility", "Swallowing assessment"],
                "focus_areas": ["bed mobility", "sitting balance", "passive ROM", "cognitive awareness"]
            },
            "subacute": {
                "name": "Subacute / Early Recovery",
                "duration_weeks": 12,
                "goals": ["Restore motor function", "Improve balance", "ADL training", "Cognitive recovery"],
                "focus_areas": ["active ROM", "standing balance", "gait training", "fine motor", "attention exercises"]
            },
            "chronic": {
                "name": "Chronic / Long-term Recovery",
                "duration_weeks": None,
                "goals": ["Maximize independence", "Community reintegration", "Prevent decline"],
                "focus_areas": ["advanced mobility", "complex tasks", "social participation", "fitness maintenance"]
            }
        }

        self.motor_exercises = {
            "upper_extremity": [
                {
                    "id": "ue_001",
                    "name": "Shoulder Flexion Assist",
                    "description": "Use unaffected hand to assist raising affected arm overhead",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "10 reps x 3 sets",
                    "hold": "5 seconds",
                    "muscle_group": "deltoid, supraspinatus",
                    "contraindications": ["shoulder subluxation without sling support"],
                    "neural_pathway": "corticospinal tract facilitation"
                },
                {
                    "id": "ue_002",
                    "name": "Wrist Extension with Gravity Elimination",
                    "description": "Side-lying position, extend wrist toward ceiling",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "15 reps x 3 sets",
                    "hold": "3 seconds",
                    "muscle_group": "wrist extensors",
                    "neural_pathway": "radial nerve re-education"
                },
                {
                    "id": "ue_003",
                    "name": "Finger-to-Nose Coordination",
                    "description": "Touch nose with affected hand, progressively increase speed",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "10 reps each hand",
                    "muscle_group": "shoulder, elbow, wrist coordination",
                    "neural_pathway": "cerebellar coordination"
                },
                {
                    "id": "ue_004",
                    "name": "Cylinder Grasp Training",
                    "description": "Grasp and release objects of increasing size",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "20 reps x 2 sets",
                    "muscle_group": "flexor digitorum",
                    "neural_pathway": "median/ulnar nerve recovery"
                },
                {
                    "id": "ue_005",
                    "name": "Weight Bearing Through Affected Arm",
                    "description": "Bilateral weight bearing in sitting, progress to modified push-up position",
                    "difficulty": "intermediate",
                    "phase": ["subacute"],
                    "reps": "Hold 30 seconds x 3",
                    "muscle_group": "shoulder stabilizers, core",
                    "neural_pathway": "proprioceptive facilitation"
                },
                {
                    "id": "ue_006",
                    "name": "Pronation/Supination with Weight",
                    "description": "Rotate forearm with 1lb weight, palm up to palm down",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "12 reps x 3 sets",
                    "muscle_group": "pronator teres, supinator",
                    "neural_pathway": "bilateral coordination"
                },
                {
                    "id": "ue_007",
                    "name": "Bilateral Upper Extremity Coordination",
                    "description": "Clap, roll ball between hands, table top exercises",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "5 minutes",
                    "muscle_group": "bilateral coordination",
                    "neural_pathway": "interhemispheric communication"
                }
            ],
            "lower_extremity": [
                {
                    "id": "le_001",
                    "name": "Ankle Pumps",
                    "description": "Dorsiflex and plantarflex ankle rhythmically",
                    "difficulty": "beginner",
                    "phase": ["acute"],
                    "reps": "20 reps x 4 sets daily",
                    "muscle_group": "tibialis anterior, gastrocnemius",
                    "prevention": "DVT prevention",
                    "neural_pathway": "L4-S1 nerve root activation"
                },
                {
                    "id": "le_002",
                    "name": "Heel Slides",
                    "description": "Slide heel toward buttocks in supine, control the return",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "10 reps x 3 sets",
                    "muscle_group": "hip flexors, knee flexors",
                    "neural_pathway": "femoral nerve facilitation"
                },
                {
                    "id": "le_003",
                    "name": "Bridging",
                    "description": "Lift hips off bed, hold, lower slowly",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "10 reps x 3 sets, 5-sec hold",
                    "muscle_group": "glutes, hamstrings, core",
                    "neural_pathway": "sacroiliac stabilization"
                },
                {
                    "id": "le_004",
                    "name": "Standing Hip Abduction",
                    "description": "Lift affected leg to side while holding support",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "10 reps x 3 sets",
                    "muscle_group": "gluteus medius",
                    "neural_pathway": "superior gluteal nerve re-education"
                },
                {
                    "id": "le_005",
                    "name": "Step-Ups",
                    "description": "Step up onto 4-inch step, progress height over time",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "10 reps each leg x 2 sets",
                    "muscle_group": "quadriceps, glutes",
                    "neural_pathway": "weight acceptance pattern"
                },
                {
                    "id": "le_006",
                    "name": "Tandem Walking",
                    "description": "Walk heel-to-toe along a line",
                    "difficulty": "advanced",
                    "phase": ["chronic"],
                    "reps": "20 feet x 3",
                    "muscle_group": "peroneals, tibialis posterior",
                    "neural_pathway": "cerebellar balance pathways"
                },
                {
                    "id": "le_007",
                    "name": "Single Leg Stance",
                    "description": "Stand on affected leg, progress time from 5 to 30 seconds",
                    "difficulty": "advanced",
                    "phase": ["subacute", "chronic"],
                    "reps": "Hold 10-30 seconds x 5",
                    "muscle_group": "ankle stabilizers, hip stabilizers",
                    "neural_pathway": "proprioceptive integration"
                }
            ],
            "core_balance": [
                {
                    "id": "cb_001",
                    "name": "Seated Balance Reaching",
                    "description": "Reach forward, sideways, and diagonally while seated",
                    "difficulty": "beginner",
                    "phase": ["acute", "subacute"],
                    "reps": "10 reaches each direction x 2",
                    "muscle_group": "obliques, transversus abdominis"
                },
                {
                    "id": "cb_002",
                    "name": "Standing Weight Shifts",
                    "description": "Shift weight side to side and forward-back while standing",
                    "difficulty": "intermediate",
                    "phase": ["subacute", "chronic"],
                    "reps": "15 shifts each direction x 3",
                    "muscle_group": "hip abductors/adductors, core"
                },
                {
                    "id": "cb_003",
                    "name": "Perturbation Training",
                    "description": "Stand on foam pad while therapist provides gentle pushes",
                    "difficulty": "advanced",
                    "phase": ["chronic"],
                    "reps": "2 minutes x 3",
                    "muscle_group": "full body reactive balance"
                }
            ]
        }

        self.cognitive_exercises = {
            "attention": [
                {
                    "id": "at_001",
                    "name": "Sustained Attention Task",
                    "description": "Watch a moving dot and tap when it changes color",
                    "difficulty": "beginner",
                    "duration_minutes": 5,
                    "cognitive_domain": "sustained attention",
                    "target_area": "right frontal-parietal network"
                },
                {
                    "id": "at_002",
                    "name": "Alternating Attention Switch",
                    "description": "Switch between counting forward and alphabet alternately",
                    "difficulty": "intermediate",
                    "duration_minutes": 10,
                    "cognitive_domain": "alternating attention",
                    "target_area": "prefrontal cortex"
                },
                {
                    "id": "at_003",
                    "name": "Visual Scanning Search",
                    "description": "Find specific items in a busy visual scene",
                    "difficulty": "beginner",
                    "duration_minutes": 8,
                    "cognitive_domain": "selective attention",
                    "target_area": "parietal lobe (spatial neglect)"
                }
            ],
            "memory": [
                {
                    "id": "me_001",
                    "name": "Picture-Word Association",
                    "description": "Match pictures with written words, progress to delayed recall",
                    "difficulty": "beginner",
                    "duration_minutes": 10,
                    "cognitive_domain": "verbal memory",
                    "target_area": "hippocampus, temporal lobe"
                },
                {
                    "id": "me_002",
                    "name": "Sequential Number Memory",
                    "description": "Remember increasing sequences of numbers (digit span)",
                    "difficulty": "intermediate",
                    "duration_minutes": 8,
                    "cognitive_domain": "working memory",
                    "target_area": "dorsolateral prefrontal cortex"
                },
                {
                    "id": "me_003",
                    "name": "Grocery List Recall",
                    "description": "Memorize a grocery list, recall after a delay",
                    "difficulty": "intermediate",
                    "duration_minutes": 10,
                    "cognitive_domain": "functional memory",
                    "target_area": "hippocampal formation"
                }
            ],
            "executive_function": [
                {
                    "id": "ef_001",
                    "name": "Task Sequencing",
                    "description": "Put daily activities in correct order (morning routine)",
                    "difficulty": "beginner",
                    "duration_minutes": 10,
                    "cognitive_domain": "sequencing",
                    "target_area": "frontal lobe"
                },
                {
                    "id": "ef_002",
                    "name": "Decision Making Scenarios",
                    "description": "Choose the best response in social/practical scenarios",
                    "difficulty": "intermediate",
                    "duration_minutes": 15,
                    "cognitive_domain": "problem solving",
                    "target_area": "orbitofrontal cortex"
                },
                {
                    "id": "ef_003",
                    "name": "Goal Setting & Planning",
                    "description": "Break a larger goal into daily actionable steps",
                    "difficulty": "intermediate",
                    "duration_minutes": 15,
                    "cognitive_domain": "planning, organization",
                    "target_area": "anterior cingulate cortex"
                }
            ],
            "neglect_training": [
                {
                    "id": "nt_001",
                    "name": "Left Visual Field Scanning",
                    "description": "Systematically scan from right to left, attending to neglected side",
                    "difficulty": "beginner",
                    "duration_minutes": 10,
                    "cognitive_domain": "spatial awareness",
                    "target_area": "right parietal lobe"
                },
                {
                    "id": "nt_002",
                    "name": "Mirror Therapy",
                    "description": "Use mirror to create illusion of affected limb movement",
                    "difficulty": "beginner",
                    "duration_minutes": 15,
                    "cognitive_domain": "body schema, motor imagery",
                    "target_area": "premotor cortex, mirror neuron system"
                }
            ]
        }

        self.speech_exercises = {
            "aphasia": [
                {
                    "id": "sa_001",
                    "name": "Naming Practice with Categories",
                    "description": "Name objects by category (fruits, animals, household items)",
                    "difficulty": "beginner",
                    "aphasia_type": "anomic",
                    "technique": "semantic feature analysis"
                },
                {
                    "id": "sa_002",
                    "name": "Sentence Completion",
                    "description": "Complete sentences with appropriate words",
                    "difficulty": "beginner",
                    "aphasia_type": "all types",
                    "technique": "constrain production"
                },
                {
                    "id": "sa_003",
                    "name": "Conversational Script Training",
                    "description": "Practice common daily conversations (ordering food, greetings)",
                    "difficulty": "intermediate",
                    "aphasia_type": "broca's, global",
                    "technique": "script training"
                }
            ],
            "dysarthria": [
                {
                    "id": "dy_001",
                    "name": "Articulation Drills",
                    "description": "Exaggerate consonant production with visual feedback",
                    "difficulty": "beginner",
                    "technique": "Lee Silverman Voice Treatment (LSVT) principles"
                },
                {
                    "id": "dy_002",
                    "name": "Breath Control for Speech",
                    "description": "Sustained phonation, phrase length exercises",
                    "difficulty": "intermediate",
                    "technique": "respiratory-phonatory coordination"
                }
            ],
            "apraxia": [
                {
                    "id": "ap_001",
                    "name": "Sequential Movement Practice",
                    "description": "Repeat tongue/lip sequences with cues",
                    "difficulty": "beginner",
                    "technique": "prompts for motor planning"
                },
                {
                    "id": "ap_002",
                    "name": "Over-Articulation Drill",
                    "description": "Exaggerate mouth movements for target sounds",
                    "difficulty": "intermediate",
                    "technique": "articulatory kinematic approach"
                }
            ]
        }

        self.fitness_programs = {
            "cardiovascular": [
                {"name": "Seated Marching", "intensity": "low", "duration": "10 min", "phase": ["acute"]},
                {"name": "Arm Ergometry", "intensity": "low-moderate", "duration": "15 min", "phase": ["subacute"]},
                {"name": "Treadmill Walking", "intensity": "moderate", "duration": "20 min", "phase": ["subacute", "chronic"]},
                {"name": "Stationary Cycling", "intensity": "moderate", "duration": "20 min", "phase": ["subacute", "chronic"]},
                {"name": "Elliptical Trainer", "intensity": "moderate-high", "duration": "25 min", "phase": ["chronic"]}
            ],
            "strength": [
                {"name": "Resistance Band Upper Body", "intensity": "low", "sets": "2x10", "phase": ["subacute"]},
                {"name": "Bodyweight Squats", "intensity": "moderate", "sets": "2x8", "phase": ["subacute"]},
                {"name": "Dumbbell Circuit", "intensity": "moderate", "sets": "3x12", "phase": ["chronic"]},
                {"name": "Functional Training Circuit", "intensity": "moderate-high", "sets": "3x10", "phase": ["chronic"]}
            ],
            "flexibility": [
                {"name": "Passive ROM Exercises", "intensity": "gentle", "duration": "15 min", "phase": ["acute"]},
                {"name": "Active-Assisted Stretching", "intensity": "gentle", "duration": "15 min", "phase": ["subacute"]},
                {"name": "Yoga for Stroke Survivors", "intensity": "moderate", "duration": "30 min", "phase": ["chronic"]}
            ]
        }

        self.brain_exercises = [
            {
                "name": "Dual N-Back",
                "description": "Track visual and auditory stimuli simultaneously",
                "neuroplasticity_target": "working memory, fluid intelligence",
                "evidence_level": "strong"
            },
            {
                "name": "Clock Drawing Task",
                "description": "Draw a clock with specific time, assesses visuospatial skills",
                "neuroplasticity_target": "visuospatial, executive function",
                "evidence_level": "strong"
            },
            {
                "name": "Category Fluency",
                "description": "Name as many items in a category as possible in 60 seconds",
                "neuroplasticity_target": "language retrieval, semantic memory",
                "evidence_level": "moderate"
            },
            {
                "name": "Mental Rotation Tasks",
                "description": "Mentally rotate objects to match target orientation",
                "neuroplasticity_target": "visuospatial processing, parietal lobe",
                "evidence_level": "moderate"
            },
            {
                "name": "Musical Rhythm Training",
                "description": "Tap along to rhythms, progress to complex patterns",
                "neuroplasticity_target": "rhythm, timing, cerebellar function",
                "evidence_level": "moderate"
            },
            {
                "name": "Bilateral Coordination Drums",
                "description": "Drum with both hands in alternating and simultaneous patterns",
                "neuroplasticity_target": "bilateral coordination, interhemispheric transfer",
                "evidence_level": "moderate"
            }
        ]

    def get_rehab_plan(self, stroke_date: str, affected_side: str, deficits: List[str]) -> Dict:
        """Generate personalized rehabilitation plan"""
        stroke_dt = datetime.fromisoformat(stroke_date)
        weeks_since = (datetime.now() - stroke_dt).days / 7

        if weeks_since <= 4:
            current_phase = "acute"
        elif weeks_since <= 16:
            current_phase = "subacute"
        else:
            current_phase = "chronic"

        phase_info = self.rehab_phases[current_phase]
        plan = {
            "current_phase": current_phase,
            "phase_name": phase_info["name"],
            "weeks_since_stroke": round(weeks_since, 1),
            "affected_side": affected_side,
            "goals": phase_info["goals"],
            "motor_exercises": [],
            "cognitive_exercises": [],
            "speech_exercises": [],
            "fitness_program": [],
            "weekly_schedule": {},
            "milestones": [],
            "red_flags": [
                "Sudden severe headache",
                "New weakness or numbness",
                "Difficulty speaking or understanding",
                "Vision changes",
                "Loss of balance or coordination",
                "Chest pain or shortness of breath"
            ]
        }

        # Filter exercises by phase and affected side
        for category, exercises in self.motor_exercises.items():
            for ex in exercises:
                if current_phase in ex.get("phase", []):
                    plan["motor_exercises"].append({**ex, "category": category})

        # Add cognitive exercises relevant to deficits
        for deficit in deficits:
            if deficit in self.cognitive_exercises:
                plan["cognitive_exercises"].extend(self.cognitive_exercises[deficit])
            if deficit in self.speech_exercises:
                plan["speech_exercises"].extend(self.speech_exercises[deficit])

        # Fitness program
        for category, programs in self.fitness_programs.items():
            for prog in programs:
                if current_phase in prog.get("phase", []):
                    plan["fitness_program"].append({**prog, "category": category})

        # Brain exercises
        plan["brain_exercises"] = self.brain_exercises[:4]

        # Generate weekly schedule
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            plan["weekly_schedule"][day] = {
                "morning": "Motor exercises (30 min)",
                "midday": "Cognitive exercises (20 min)" if plan["cognitive_exercises"] else "Rest",
                "afternoon": "Fitness session (20-30 min)",
                "evening": "Speech exercises (15 min)" if plan["speech_exercises"] else "Relaxation"
            }
            if day in ["Saturday", "Sunday"]:
                plan["weekly_schedule"][day]["morning"] = "Light activity / rest"

        # Milestones
        milestones_by_phase = {
            "acute": [
                "Independently turn in bed",
                "Sit at edge of bed without support",
                "Transfer to wheelchair with assistance",
                "Feed self with adaptive utensils"
            ],
            "subacute": [
                "Stand independently for 30 seconds",
                "Walk 50 feet with assistive device",
                "Button shirt independently",
                "Write name legibly",
                "Follow 2-step verbal commands",
                "Express wants/needs verbally"
            ],
            "chronic": [
                "Walk without assistive device",
                "Climb stairs with rail",
                "Drive screening assessment",
                "Return to work/volunteer activities",
                "Participate in community activities",
                "Exercise independently 3x/week"
            ]
        }
        plan["milestones"] = milestones_by_phase[current_phase]

        return plan

    def assess_progress(self, session_data: List[Dict]) -> Dict:
        """Analyze rehabilitation progress over time"""
        if not session_data:
            return {"status": "no_data", "message": "No session data available"}

        total_sessions = len(session_data)
        dates = [s.get("date") for s in session_data if "date" in s]

        # Calculate average scores
        motor_scores = [s.get("motor_score", 0) for s in session_data if "motor_score" in s]
        cognitive_scores = [s.get("cognitive_score", 0) for s in session_data if "cognitive_score" in s]
        balance_scores = [s.get("balance_score", 0) for s in session_data if "balance_score" in s]

        def trend(values):
            if len(values) < 2:
                return "insufficient_data"
            recent = sum(values[-3:]) / min(3, len(values))
            earlier = sum(values[:3]) / min(3, len(values))
            diff = recent - earlier
            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            return "stable"

        return {
            "total_sessions": total_sessions,
            "date_range": {"first": dates[0] if dates else None, "last": dates[-1] if dates else None},
            "motor_progress": {
                "average": round(sum(motor_scores) / len(motor_scores), 1) if motor_scores else 0,
                "latest": motor_scores[-1] if motor_scores else 0,
                "trend": trend(motor_scores)
            },
            "cognitive_progress": {
                "average": round(sum(cognitive_scores) / len(cognitive_scores), 1) if cognitive_scores else 0,
                "latest": cognitive_scores[-1] if cognitive_scores else 0,
                "trend": trend(cognitive_scores)
            },
            "balance_progress": {
                "average": round(sum(balance_scores) / len(balance_scores), 1) if balance_scores else 0,
                "latest": balance_scores[-1] if balance_scores else 0,
                "trend": trend(balance_scores)
            },
            "consistency_score": min(100, round((total_sessions / max(1, (datetime.now() - datetime.fromisoformat(dates[0])).days)) * 7 * 100)) if dates else 0,
            "recommendations": []
        }

    def get_exercise_for_deficit(self, deficit_type: str, severity: str) -> List[Dict]:
        """Get targeted exercises for specific deficit"""
        exercises = []

        if deficit_type in self.cognitive_exercises:
            exercises = self.cognitive_exercises[deficit_type]

        if deficit_type in self.speech_exercises:
            exercises.extend(self.speech_exercises[deficit_type])

        # Filter by severity
        if severity == "mild":
            exercises = [e for e in exercises if e.get("difficulty") in ["beginner", "intermediate"]]
        elif severity == "moderate":
            exercises = [e for e in exercises if e.get("difficulty") == "beginner"]

        return exercises

    def get_neuroplasticity_tips(self) -> List[Dict]:
        """Get evidence-based neuroplasticity optimization tips"""
        return [
            {
                "tip": "Intensive, repetitive practice drives neuroplasticity",
                "detail": "Repeat exercises many times per session; neuroplasticity requires high repetition",
                "evidence": "Kleim & Jones, 2008 - Principles of Experience-Dependent Neural Plasticity"
            },
            {
                "tip": "Salience matters — make exercises meaningful",
                "detail": "Choose activities that matter to the patient personally for greater neural change",
                "evidence": "Lovejoy et al., 2016"
            },
            {
                "tip": "Practice when fatigued is counterproductive",
                "detail": "Stop before fatigue sets in; rested practice creates stronger neural pathways",
                "evidence": "Langhorne et al., 2011"
            },
            {
                "tip": "Task-specific training transfers better than general exercises",
                "detail": "Practice actual tasks (reaching for cup) rather than abstract movements",
                "evidence": "Lohse et al., 2014"
            },
            {
                "tip": "Feedback accelerates motor learning",
                "detail": "Use visual, auditory, or tactile feedback during exercises",
                "evidence": "Winstein & Schmidt, 1990"
            },
            {
                "tip": "Distributed practice beats massed practice",
                "detail": "Shorter, more frequent sessions (30-45 min) outperform long marathon sessions",
                "evidence": "Sale & de Boer, 2020"
            },
            {
                "tip": "Constraint-Induced Movement Therapy (CIMT)",
                "detail": "Restraining the unaffected limb forces use of affected limb, driving cortical reorganization",
                "evidence": "Taub et al., 2006"
            }
        ]


stroke_rehab_service = StrokeRehabService()
