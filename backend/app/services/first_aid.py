"""
Emergency First Aid Guide & Disaster Health Preparedness Service
Step-by-step emergency guidance, CPR training, disaster preparedness
"""
from datetime import datetime
from typing import Dict, List, Optional, Any


class FirstAidService:
    """Comprehensive emergency first aid and disaster preparedness platform"""

    def __init__(self):
        self.emergency_protocols = {
            "cardiac_arrest": {
                "name": "Cardiac Arrest — CPR & AED",
                "severity": "life-threatening",
                "icon": "❤️",
                "steps": [
                    {"step": 1, "action": "Check responsiveness", "detail": "Tap shoulders and shout 'Are you OK?'", "time": "5 seconds"},
                    {"step": 2, "action": "Call 911 / activate emergency response", "detail": "If alone, put phone on speaker", "time": "10 seconds"},
                    {"step": 3, "action": "Check breathing", "detail": "Look for chest rise for 10 seconds", "time": "10 seconds"},
                    {"step": 4, "action": "Begin chest compressions", "detail": "Heel of hand on center of chest, push hard and fast, 100-120/min, full recoil", "time": "until AED"},
                    {"step": 5, "action": "Deliver 30 compressions", "detail": "30:2 ratio if trained, compression-only if untrained", "time": "about 15 seconds"},
                    {"step": 6, "action": "Use AED when available", "detail": "Turn on AED, follow voice prompts, ensure no one touching patient", "time": "immediately"},
                    {"step": 7, "action": "Continue until EMS arrives", "detail": "Switch compressors every 2 minutes to prevent fatigue", "time": "continuous"}
                ],
                "key_points": [
                    "Push hard (at least 2 inches) and fast (100-120/min)",
                    "Allow full chest recoil between compressions",
                    "Minimize interruptions in compressions",
                    "Compression-only CPR is effective for untrained bystanders",
                    "AED use dramatically improves survival — use it as soon as available"
                ],
                "common_mistakes": [
                    "Compressing too shallow",
                    "Allowing incomplete chest recoil",
                    "Excessive ventilation pauses",
                    "Not pushing hard enough"
                ]
            },
            "choking_adult": {
                "name": "Choking — Conscious Adult",
                "severity": "life-threatening",
                "icon": "🫁",
                "steps": [
                    {"step": 1, "action": "Assess severity", "detail": "Can they cough, speak, breathe? If yes, encourage coughing", "time": "immediate"},
                    {"step": 2, "action": "If cannot cough/breathe/speak", "detail": "Stand behind person, wrap arms around waist", "time": "immediate"},
                    {"step": 3, "action": "Perform abdominal thrusts (Heimlich)", "detail": "Make fist above navel, thrust inward and upward", "time": "repeat"},
                    {"step": 4, "action": "Repeat until object expelled or person becomes unconscious", "detail": "Each thrust should be a separate attempt", "time": "as needed"},
                    {"step": 5, "action": "If unconscious: lower to ground, begin CPR", "detail": "Look in mouth before each breath, remove visible object", "time": "immediate"}
                ],
                "key_points": [
                    "Ask 'Are you choking? Can you speak?' first",
                    "For pregnant or obese persons: chest thrusts instead of abdominal",
                    "Self-administered: make a fist above navel, thrust inward and upward",
                    "Infants (<1 year): 5 back slaps + 5 chest thrusts"
                ]
            },
            "severe_bleeding": {
                "name": "Severe Bleeding Control",
                "severity": "life-threatening",
                "icon": "🩸",
                "steps": [
                    {"step": 1, "action": "Ensure scene safety", "detail": "Put on gloves if available", "time": "5 seconds"},
                    {"step": 2, "action": "Apply direct pressure", "detail": "Use clean cloth, press firmly on wound", "time": "immediate"},
                    {"step": 3, "action": "Do not remove blood-soaked cloths", "detail": "Add more layers on top", "time": "ongoing"},
                    {"step": 4, "action": "If bleeding doesn't stop, apply tourniquet", "detail": "Place 2-3 inches above wound, tighten until bleeding stops, note time", "time": "if needed"},
                    {"step": 5, "action": "Elevate the injured limb above heart level", "detail": "While maintaining pressure", "time": "ongoing"},
                    {"step": 6, "action": "Keep person warm, treat for shock", "detail": "Cover with blanket, elevate legs if no spinal injury", "time": "ongoing"}
                ],
                "key_points": [
                    "Apply firm, continuous pressure for at least 10 minutes",
                    "Tourniquets save lives — don't be afraid to use one",
                    "Note the time of tourniquet application",
                    "Remove clothing from around the wound"
                ]
            },
            "stroke": {
                "name": "Stroke Recognition & Response (FAST)",
                "severity": "life-threatening",
                "icon": "🧠",
                "steps": [
                    {"step": 1, "action": "F — Face drooping", "detail": "Ask person to smile. Is one side drooping?", "time": "30 seconds"},
                    {"step": 2, "action": "A — Arm weakness", "detail": "Ask person to raise both arms. Does one drift down?", "time": "30 seconds"},
                    {"step": 3, "action": "S — Speech difficulty", "detail": "Ask person to repeat a simple sentence. Is speech slurred?", "time": "30 seconds"},
                    {"step": 4, "action": "T — Time to call 911", "detail": "Note exact time symptoms began — critical for treatment", "time": "immediate"},
                    {"step": 5, "action": "Monitor and keep safe", "detail": "Keep person calm, lying on affected side if vomiting, do NOT give food/drink", "time": "until EMS"}
                ],
                "key_points": [
                    "Time is brain — every minute counts",
                    "Do NOT drive to hospital yourself — call 911",
                    "Note the exact time symptoms started",
                    "Do NOT give aspirin (could be hemorrhagic stroke)",
                    "Keep airway clear if vomiting"
                ]
            },
            "burns": {
                "name": "Burns — First Aid",
                "severity": "moderate",
                "icon": "🔥",
                "steps": [
                    {"step": 1, "action": "Remove from heat source", "detail": "Stop the burning process", "time": "immediate"},
                    {"step": 2, "action": "Cool the burn", "detail": "Run cool (not ice cold) water for 10-20 minutes", "time": "10-20 min"},
                    {"step": 3, "action": "Remove jewelry/clothing", "detail": "From burned area, unless stuck to skin", "time": "after cooling"},
                    {"step": 4, "action": "Cover with sterile dressing", "detail": "Do NOT use butter, toothpaste, or home remedies", "time": "after cooling"},
                    {"step": 5, "action": "Take pain relief if needed", "detail": "Ibuprofen or acetaminophen", "time": "as needed"}
                ],
                "key_points": [
                    "Cool with running water for 10-20 minutes",
                    "NEVER use ice, butter, toothpaste, or oil on burns",
                    "For chemical burns: flush with large amounts of water for 20+ minutes",
                    "For electrical burns: do NOT touch person if still in contact with source",
                    "Seek emergency care for burns larger than palm, on face/hands/joints, or circumferential"
                ],
                "severity_levels": [
                    {"level": "First degree", "description": "Red, painful, no blisters (sunburn-like)", "treatment": "Cool water, aloe vera, OTC pain relief"},
                    {"level": "Second degree", "description": "Red, blistered, very painful", "treatment": "Cool water, sterile dressing, seek medical care"},
                    {"level": "Third degree", "description": "White/charred, may be painless (nerve damage)", "treatment": "Cover, call 911 immediately"}
                ]
            },
            "allergic_reaction": {
                "name": "Anaphylaxis — Severe Allergic Reaction",
                "severity": "life-threatening",
                "icon": "⚠️",
                "steps": [
                    {"step": 1, "action": "Recognize symptoms", "detail": "Hives, swelling (face/throat), difficulty breathing, rapid pulse, dizziness", "time": "immediate"},
                    {"step": 2, "action": "Administer epinephrine auto-injector (EpiPen)", "detail": "Outer thigh (through clothing if needed), hold 10 seconds", "time": "immediate"},
                    {"step": 3, "action": "Call 911", "detail": "Even after EpiPen, anaphylaxis can recur", "time": "immediately"},
                    {"step": 4, "action": "Lay person flat, elevate legs", "detail": "Unless breathing is difficult — then allow them to sit up", "time": "ongoing"},
                    {"step": 5, "action": "Second dose if no improvement", "detail": "After 5-15 minutes if symptoms persist", "time": "5-15 min"},
                    {"step": 6, "action": "Begin CPR if needed", "detail": "If person stops breathing", "time": "if needed"}
                ],
                "key_points": [
                    "EpiPen first, 911 second (but do both)",
                    "EpiPen goes in outer thigh — can inject through clothing",
                    "Always call 911 even after EpiPen — biphasic reaction possible",
                    "Common triggers: peanuts, tree nuts, shellfish, bee stings, medications, latex"
                ]
            },
            "fainting": {
                "name": "Fainting (Syncope)",
                "severity": "low",
                "icon": "💫",
                "steps": [
                    {"step": 1, "action": "Lower person to ground", "detail": "If they appear about to faint", "time": "immediate"},
                    {"step": 2, "action": "Elevate legs", "detail": "About 12 inches above heart", "time": "immediate"},
                    {"step": 3, "action": "Check for injuries", "detail": "Look for head injury from fall", "time": "after safe"},
                    {"step": 4, "action": "Loosen tight clothing", "detail": "Collar, belt, tie", "time": "immediate"},
                    {"step": 5, "action": "Do NOT put anything in mouth", "detail": "Myth: they won't swallow tongue", "time": "important"}
                ],
                "key_points": [
                    "Most fainting is harmless but can indicate serious conditions",
                    "Seek medical care if: first faint, chest pain, prolonged unconsciousness, injury",
                    "Warning signs: lightheadedness, nausea, tunnel vision, sweating"
                ]
            },
            "heat_emergency": {
                "name": "Heat-Related Emergencies",
                "severity": "moderate to life-threatening",
                "icon": "🌡️",
                "types": [
                    {
                        "name": "Heat Cramps",
                        "symptoms": ["Muscle cramps", "Heavy sweating"],
                        "treatment": ["Rest in cool area", "Drink water or electrolyte beverage", "Gentle stretching", "Cool compresses"]
                    },
                    {
                        "name": "Heat Exhaustion",
                        "symptoms": ["Heavy sweating", "Cold/pale/clammy skin", "Weak/pulse", "Nausea", "Headache", "Dizziness"],
                        "treatment": ["Move to cool environment", "Loosen clothing", "Cool wet cloths on neck/armpits/groin", "Sip water", "If vomiting → 911"]
                    },
                    {
                        "name": "Heat Stroke (EMERGENCY)",
                        "symptoms": ["High body temp >103°F", "Hot/red/dry skin", "Rapid strong pulse", "Loss of consciousness"],
                        "treatment": ["CALL 911 IMMEDIATELY", "Move to cooler area", "Cool rapidly with any means (ice, cold water)", "Do NOT give fluids if unconscious", "Monitor breathing"]
                    }
                ]
            },
            "hypothermia": {
                "name": "Hypothermia — Cold Emergency",
                "severity": "life-threatening",
                "icon": "🥶",
                "steps": [
                    {"step": 1, "action": "Move to warm shelter", "detail": "Remove wet clothing", "time": "immediate"},
                    {"step": 2, "action": "Warm center first", "detail": "Neck, head, chest, groin — use skin-to-skin contact if needed", "time": "immediate"},
                    {"step": 3, "action": "Give warm, sweet beverages", "detail": "Only if conscious and able to swallow", "time": "ongoing"},
                    {"step": 4, "action": "Handle gently", "detail": "Rough movement can cause cardiac arrest", "time": "always"},
                    {"step": 5, "action": "Call 911 if severe", "detail": "Confusion, slurred speech, drowsiness, loss of consciousness", "time": "if severe"}
                ]
            },
            "fractures": {
                "name": "Fracture & Sprain Management",
                "severity": "moderate",
                "icon": "🦴",
                "steps": [
                    {"step": 1, "action": "Do NOT move the injured area", "detail": "Splint in position found", "time": "immediate"},
                    {"step": 2, "action": "Immobilize the joint", "detail": "Splint above and below the injury", "time": "immediate"},
                    {"step": 3, "action": "Apply ice wrapped in cloth", "detail": "20 minutes on, 20 minutes off", "time": "ongoing"},
                    {"step": 4, "action": "Elevate above heart level", "detail": "If possible without moving fracture", "time": "ongoing"},
                    {"step": 5, "action": "Check circulation", "detail": "Feel for pulse, check color/warmth below injury", "time": "immediate"}
                ],
                "red_flags": [
                    "Open fracture (bone protruding through skin)",
                    "Loss of pulse below injury",
                    "Numbness or tingling below injury",
                    "Visible deformity",
                    "Inability to move fingers/toes"
                ]
            }
        }

        self.cpr_training = {
            "adult_cpr": {
                "name": "Adult CPR (Age 12+)",
                "steps": [
                    "Check scene safety",
                    "Check responsiveness — tap and shout",
                    "Call 911 or send someone",
                    "Open airway (head tilt-chin lift)",
                    "Check breathing (look, listen, feel — 10 seconds)",
                    "Begin compressions: 30 compressions",
                    "Give 2 rescue breaths (if trained)",
                    "Continue 30:2 until EMS arrives or AED available"
                ],
                "compression_details": {
                    "rate": "100-120 per minute (tempo of Stayin' Alive)",
                    "depth": "At least 2 inches (5 cm) for adults",
                    "recoil": "Allow full chest recoil between compressions",
                    "hand_placement": "Heel of one hand on center of chest (lower half of sternum), other hand on top"
                },
                "duration_minutes": 10
            },
            "child_cpr": {
                "name": "Child CPR (Age 1-12)",
                "steps": [
                    "Check scene safety",
                    "Check responsiveness",
                    "Call 911",
                    "Open airway",
                    "Check breathing",
                    "Begin compressions: 30 compressions (or 15:2 if 2 rescuers)",
                    "Give 2 rescue breaths",
                    "Continue until help arrives"
                ],
                "compression_details": {
                    "rate": "100-120 per minute",
                    "depth": "About 2 inches (5 cm) — one-third AP diameter",
                    "hand_placement": "One or two hands on lower half of sternum"
                }
            },
            "infant_cpr": {
                "name": "Infant CPR (Age <1)",
                "steps": [
                    "Check responsiveness — flick sole of foot",
                    "Call 911",
                    "Open airway (neutral position)",
                    "Check breathing",
                    "Begin compressions: 30 compressions",
                    "Give 2 rescue breaths (mouth over nose AND mouth)",
                    "Continue until help arrives"
                ],
                "compression_details": {
                    "rate": "100-120 per minute",
                    "depth": "About 1.5 inches (4 cm) — one-third AP diameter",
                    "hand_placement": "Two fingers on sternum, just below nipple line"
                }
            },
            "aed_usage": {
                "name": "Automated External Defibrillator (AED)",
                "steps": [
                    "Turn on AED",
                    "Expose chest, dry if wet",
                    "Apply pads: one upper right chest, one lower left side",
                    "Ensure no one is touching patient",
                    "AED analyzes rhythm — stay clear",
                    "If shock advised: shout 'CLEAR', deliver shock",
                    "Immediately resume CPR for 2 minutes",
                    "AED will re-analyze every 2 minutes"
                ],
                "special_situations": [
                    "Wet environment: dry chest, place AED on dry surface",
                    "Pacemaker: avoid placing pad directly over lump",
                    "Medication patches: remove if possible, avoid placing pad on top",
                    "Children 1-8: use pediatric pads if available, otherwise adult pads",
                    "Pregnancy: use AED normally"
                ]
            }
        }

        self.disaster_preparedness = {
            "home_kit": {
                "name": "Emergency Supply Kit",
                "essential_items": [
                    {"item": "Water", "amount": "1 gallon per person per day (3-day supply minimum)"},
                    {"item": "Non-perishable food", "amount": "3-day supply (canned goods, energy bars, dried fruit)"},
                    {"item": "First aid kit", "amount": "Bandages, gauze, antiseptic, medications"},
                    {"item": "Flashlight + batteries", "amount": "2 flashlights, extra batteries"},
                    {"item": "Battery-powered radio", "amount": "For emergency broadcasts"},
                    {"item": "Whistle", "amount": "To signal for help"},
                    {"item": "Dust masks", "amount": "N95 masks for air filtration"},
                    {"item": "Plastic sheeting", "amount": "For shelter/sealing windows"},
                    {"item": "Moist towelettes", "amount": "Sanitation when water unavailable"},
                    {"item": "Manual can opener", "amount": "For canned food"},
                    {"item": "Cell phone charger", "amount": "Portable battery pack"},
                    {"item": "Cash", "amount": "Small bills, ATMs may be down"},
                    {"item": "Copies of important documents", "amount": "ID, insurance, medical records in waterproof bag"},
                    {"item": "Medications", "amount": "7-day supply of prescription medications"},
                    {"item": "Blankets/sleeping bags", "amount": "One per person"}
                ]
            },
            "evacuation_plan": {
                "name": "Family Evacuation Plan",
                "steps": [
                    "Designate two meeting places: one near home, one outside neighborhood",
                    "Identify evacuation routes (primary + backup)",
                    "Know how to shut off utilities (gas, water, electricity)",
                    "Keep vehicle fuel tank at least half full",
                    "Prepare go-bags for each family member",
                    "Share plan with all family members",
                    "Practice evacuation drill twice per year"
                ]
            },
            "natural_disasters": {
                "earthquake": {
                    "during": ["Drop, Cover, Hold On", "Stay away from windows", "If outdoors: move to open area", "If driving: pull over, stop, stay in vehicle"],
                    "after": ["Check for injuries", "Check for gas leaks", "Expect aftershocks", "Monitor news/radio"]
                },
                "hurricane": {
                    "before": ["Board windows", "Stock 3-5 days of supplies", "Fill bathtubs with water", "Evacuate if ordered"],
                    "during": ["Stay indoors, away from windows", "Go to interior room", "Do NOT go outside eye wall"],
                    "after": ["Avoid floodwater", "Check for structural damage", "Document damage for insurance"]
                },
                "tornado": {
                    "during": ["Go to basement or interior room", "Get under sturdy furniture", "Cover head and neck", "Stay away from windows"],
                    "after": ["Check for injuries", "Watch for hazards (gas leaks, broken glass)", "Text, don't call to keep lines open"]
                },
                "wildfire": {
                    "before": ["Create defensible space (30 ft)", "Close all windows/doors", "Move flammable items away", "Evacuate early if ordered"],
                    "during": ["Wear long sleeves/pants", "Cover mouth with wet cloth", "Stay in vehicle if trapped", "Drive away from fire"],
                    "after": ["Check for hot spots", "Wear N95 mask (ash/smoke)", "Check water before drinking"]
                },
                "flood": {
                    "during": ["Move to higher ground", "Never walk/drive through floodwater", "6 inches can knock you down, 2 feet can carry a vehicle", "Avoid bridges over fast-moving water"],
                    "after": ["Don't return until authorities say safe", "Avoid contact with floodwater (contaminated)", "Check foundation for damage"]
                }
            },
            "cpr_recertification_schedule": {
                "healthcare_providers": "Every 2 years",
                "general_public": "Every 2 years recommended",
                "infant_caregivers": "Every 2 years"
            }
        }

        self.first_aid_kit_guide = {
            "basics": [
                "Adhesive bandages (various sizes)",
                "Sterile gauze pads (4x4 and 2x2)",
                "Medical tape",
                "Elastic bandage (ACE wrap)",
                "Triangular bandage (sling)",
                "Antiseptic wipes",
                "Antibiotic ointment",
                "Hydrogen peroxide",
                "Tweezers",
                "Scissors",
                "Disposable gloves",
                "Instant cold packs",
                "Thermometer",
                "CPR face shield"
            ],
            "medications": [
                "Ibuprofen (pain/inflammation)",
                "Acetaminophen (pain/fever)",
                "Diphenhydramine (allergic reactions)",
                "Hydrocortisone cream (rashes)",
                "Antidiarrheal medication",
                "Electrolyte packets",
                "Sunscreen",
                "Insect repellent"
            ],
            "specialty_items": [
                "Tourniquet (CAT recommended)",
                "Hemostatic gauze (QuikClot or Celox)",
                "Eye wash solution",
                "Burn gel",
                "SAM splint",
                "Pulse oximeter",
                "Blood pressure cuff"
            ]
        }

    def get_emergency_protocol(self, emergency_type: str) -> Dict:
        """Get step-by-step protocol for specific emergency"""
        if emergency_type in self.emergency_protocols:
            return self.emergency_protocols[emergency_type]
        return {"error": f"Unknown emergency type: {emergency_type}. Available: {list(self.emergency_protocols.keys())}"}

    def assess_emergency(self, symptoms: List[str]) -> Dict:
        """Triage symptoms and provide emergency guidance"""
        symptom_lower = [s.lower() for s in symptoms]

        life_threatening_signs = []
        urgent_signs = []
        guidance = []

        # Life-threatening indicators
        if any(s in symptom_lower for s in ["not breathing", "no pulse", "unconscious", "cardiac arrest"]):
            life_threatening_signs.append("Cardiac arrest suspected — begin CPR immediately")
            guidance.append(self.emergency_protocols["cardiac_arrest"])

        if any(s in symptom_lower for s in ["choking", "can't breathe", "can't speak", "airway blocked"]):
            life_threatening_signs.append("Airway obstruction suspected")
            guidance.append(self.emergency_protocols["choking_adult"])

        if any(s in symptom_lower for s in ["severe bleeding", "blood everywhere", "gushing blood"]):
            life_threatening_signs.append("Severe hemorrhage suspected")
            guidance.append(self.emergency_protocols["severe_bleeding"])

        if any(s in symptom_lower for s in ["face drooping", "arm weakness", "slurred speech", "stroke"]):
            life_threatening_signs.append("STROKE — use FAST protocol")
            guidance.append(self.emergency_protocols["stroke"])

        if any(s in symptom_lower for s in ["hives", "swollen throat", "can't breathe", "anaphylaxis", "epipen"]):
            life_threatening_signs.append("Anaphylaxis suspected")
            guidance.append(self.emergency_protocols["allergic_reaction"])

        # Urgent indicators
        if any(s in symptom_lower for s in ["burn", "scald", "fire"]):
            urgent_signs.append("Burn injury")
            guidance.append(self.emergency_protocols["burns"])

        if any(s in symptom_lower for s in ["broken bone", "fracture", "can't move", "deformed limb"]):
            urgent_signs.append("Possible fracture")
            guidance.append(self.emergency_protocols["fractures"])

        if any(s in symptom_lower for s in ["heat stroke", "hot", "confused", "overheated"]):
            urgent_signs.append("Heat emergency")
            guidance.append(self.emergency_protocols["heat_emergency"])

        if any(s in symptom_lower for s in ["cold", "shivering", "hypothermia", "frozen"]):
            urgent_signs.append("Cold emergency")
            guidance.append(self.emergency_protocols["hypothermia"])

        # Determine urgency
        if life_threatening_signs:
            urgency = "CRITICAL — Call 911 IMMEDIATELY"
            action = "Act now — follow protocol below"
        elif urgent_signs:
            urgency = "URGENT — Seek medical attention"
            action = "Follow first aid protocol, seek care"
        else:
            urgency = "Assessment inconclusive"
            action = "If symptoms are severe, call 911 or go to ER"

        return {
            "urgency_level": urgency,
            "recommended_action": action,
            "life_threatening_signs": life_threatening_signs,
            "urgent_signs": urgent_signs,
            "relevant_protocols": guidance,
            "call_911": len(life_threatening_signs) > 0
        }

    def get_cpr_training(self, age_group: str = "adult") -> Dict:
        """Get CPR training module"""
        if age_group == "adult":
            return self.cpr_training["adult_cpr"]
        elif age_group == "child":
            return self.cpr_training["child_cpr"]
        elif age_group == "infant":
            return self.cpr_training["infant_cpr"]
        return self.cpr_training

    def get_disaster_preparedness(self) -> Dict:
        """Get comprehensive disaster preparedness guide"""
        return self.disaster_preparedness

    def get_first_aid_kit(self) -> Dict:
        """Get first aid kit guide"""
        return self.first_aid_kit_guide


first_aid_service = FirstAidService()
