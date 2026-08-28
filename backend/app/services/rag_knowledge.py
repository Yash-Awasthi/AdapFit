"""
AdapFit RAG Knowledge System
Retrieval-Augmented Generation for exercise knowledge, fitness science, and coaching context.
Provides contextual knowledge to the LLM chat for evidence-based coaching responses.
"""
from typing import Dict, List, Any, Optional
import re


# Fitness science knowledge base (curated, evidence-based)
FITNESS_KNOWLEDGE = {
    "recovery_science": {
        "topics": ["HRV", "sleep", "muscle recovery", "deload", "rest days"],
        "entries": [
            {
                "topic": "HRV interpretation",
                "content": (
                    "HRV (RMSSD) reflects parasympathetic nervous system activity. "
                    "A Z-score below -1.0 relative to your 28-day baseline indicates "
                    "impaired autonomic recovery. Consistent downward HRV trends over 5+ days "
                    "may indicate accumulating fatigue, illness onset, or overtraining. "
                    "Individual baselines vary widely — always compare to YOUR personal mean."
                ),
                "source": " sports medicine literature",
                "relevance_keywords": ["hrv", "rmssd", "recovery", "autonomic", "baseline"],
            },
            {
                "topic": "Sleep and recovery",
                "content": (
                    "Sleep is the most potent recovery modality. Growth hormone peaks during "
                    "deep sleep (N3 stage). Sleep debt accumulates linearly — 2 hours deficit "
                    "tonight requires 2+ nights of adequate sleep to fully restore. "
                    "Sleep efficiency below 80% or duration below 6 hours significantly impairs "
                    "muscle protein synthesis and cognitive function."
                ),
                "source": "sleep medicine research",
                "relevance_keywords": ["sleep", "rest", "recovery", "fatigue", "tired"],
            },
            {
                "topic": "ACWR guidelines",
                "content": (
                    "The Acute:Chronic Workload Ratio (ACWR) should stay between 0.8-1.3 "
                    "for optimal training adaptation with minimal injury risk. "
                    "An ACWR above 1.5 increases injury risk by 2-4x. "
                    "The chronic load should be computed over 28 days using exponentially "
                    "weighted moving averages for the most accurate tracking."
                ),
                "source": "Gabbett (2016), British Journal of Sports Medicine",
                "relevance_keywords": ["acwr", "workload", "overtraining", "injury", "volume"],
            },
            {
                "topic": "Deload week science",
                "content": (
                    "A deload week (reducing volume by 40-60%) every 4-6 weeks allows "
                    "supercompensation — the body adapts and rebounds above previous fitness levels. "
                    "Signs you need a deload: declining HRV trend, persistent muscle soreness >3 days, "
                    "decreased motivation, sleep disruption, or ACWR >1.3 for 2+ weeks."
                ),
                "source": "periodization research",
                "relevance_keywords": ["deload", "rest", "overtraining", "fatigue", "break"],
            },
        ],
    },
    "exercise_science": {
        "topics": ["technique", "programming", "periodization", "progressive overload"],
        "entries": [
            {
                "topic": "Progressive overload",
                "content": (
                    "Progressive overload is the fundamental training principle. "
                    "Methods: increase weight 2-5%, add 1-2 reps, add a set, decrease rest, "
                    "improve technique quality, or increase training frequency. "
                    "Aim for ~2.5% load increase per week for compound lifts, 5% for isolations."
                ),
                "source": "strength and conditioning principles",
                "relevance_keywords": ["progressive", "overload", "stronger", "increase", "progress"],
            },
            {
                "topic": "Volume landmarks",
                "content": (
                    "Minimum Effective Volume (MEV): ~10 sets/muscle/week for maintenance. "
                    "Maximum Adaptive Volume (MAV): ~15-20 sets/muscle/week for most people. "
                    "Maximum Recoverable Volume (MRV): varies by individual, typically 20-25+ sets. "
                    "Training above MRV without adequate recovery leads to overtraining syndrome."
                ),
                "source": "Mike Israetel, Renaissance Periodization",
                "relevance_keywords": ["volume", "sets", "frequency", "programming", "hypertrophy"],
            },
            {
                "topic": "RPE training",
                "content": (
                    "RPE (Rate of Perceived Exertion) on a 1-10 scale is a validated tool "
                    "for autoregulating training intensity. RPE 8 = could do 2 more reps. "
                    "RPE 9 = could do 1 more rep. RPE 10 = absolute failure. "
                    "Training at RPE 7-9 is optimal for hypertrophy. RPE 9-10 should be "
                    "used sparingly (max 1-2 sets per session) to manage fatigue."
                ),
                "source": "Nunes et al., 2016",
                "relevance_keywords": ["rpe", "intensity", "effort", "failure", "autoregulation"],
            },
            {
                "topic": "Exercise selection",
                "content": (
                    "Compound movements (squat, bench, deadlift, row, overhead press) should "
                    "form the foundation of most programs. They train multiple muscle groups "
                    "simultaneously and produce the highest hormonal response. "
                    "Isolation exercises (curls, laterals, flyes) are valuable accessories "
                    "for lagging muscle groups and balanced development."
                ),
                "source": "NSCA Guidelines",
                "relevance_keywords": ["compound", "isolation", "exercise", "squat", "bench", "deadlift"],
            },
        ],
    },
    "nutrition_basics": {
        "topics": ["protein", "calories", "macros", "hydration"],
        "entries": [
            {
                "topic": "Protein requirements",
                "content": (
                    "For muscle building: 1.6-2.2g protein per kg bodyweight per day. "
                    "For fat loss/deficit: 2.0-2.4g/kg to preserve muscle mass. "
                    "Spread intake across 3-5 meals with 25-40g per meal for optimal MPS. "
                    "Post-workout protein is beneficial but total daily intake matters most."
                ),
                "source": "Morton et al., 2018, British Journal of Sports Medicine",
                "relevance_keywords": ["protein", "eat", "diet", "muscle", "nutrition"],
            },
            {
                "topic": "Hydration for performance",
                "content": (
                    "Even 2% body mass loss from dehydration impairs strength by 10-15%. "
                    "Baseline need: ~35ml per kg bodyweight daily. "
                    "During training: 400-800ml per hour depending on sweat rate and intensity. "
                    "Electrolytes (sodium, potassium, magnesium) are crucial for sessions >60 min."
                ),
                "source": "exercise physiology guidelines",
                "relevance_keywords": ["water", "hydration", "drink", "sweat", "electrolyte"],
            },
        ],
    },
    "injury_prevention": {
        "topics": ["warm-up", "cooldown", "mobility", "prehab"],
        "entries": [
            {
                "topic": "Warm-up science",
                "content": (
                    "A proper warm-up increases muscle temperature, nerve conduction velocity, "
                    "and joint lubrication. 5-10 minutes of dynamic movement (not static stretching) "
                    "reduces injury risk by up to 50%. Include: general movement → dynamic stretches "
                    "→ specific movement prep → ramp-up sets."
                ),
                "source": "sports injury prevention research",
                "relevance_keywords": ["warm", "warmup", "stretch", "injury", "prep"],
            },
            {
                "topic": "Pain vs discomfort",
                "content": (
                    "Sharp, shooting, or localized pain during exercise is a STOP signal. "
                    "Dull muscle burn and general fatigue during high reps is normal. "
                    "Joint pain (especially knees, shoulders, lower back) requires immediate "
                    "cessation and professional evaluation if it persists >48 hours. "
                    "Pain that alters movement pattern is always a red flag."
                ),
                "source": "clinical sports medicine",
                "relevance_keywords": ["pain", "hurt", "injury", "sore", "joint", "strain"],
            },
        ],
    },
    "mental_health": {
        "topics": ["motivation", "consistency", "mental health", "stress"],
        "entries": [
            {
                "topic": "Exercise and mental health",
                "content": (
                    "Exercise is a potent antidepressant: 150 min/week moderate exercise "
                    "reduces depression risk by 26-32%. Endorphins, BDNF, and serotonin "
                    "are all positively impacted. Consistency matters more than intensity — "
                    "3 moderate sessions per week beats 1 heroic session. "
                    "Rest days are productive, not lazy."
                ),
                "source": "WHO physical activity guidelines",
                "relevance_keywords": ["motivation", "mental", "depression", "anxiety", "mood", "stress"],
            },
        ],
    },
}



# Enriched knowledge entries (v2) — merged into the base at runtime
EXTRA_KNOWLEDGE = {
    # Enriched entries (v2)
    "recovery_science": {
        "entries": [
            {
                "topic": "Sleep hygiene for athletes",
                "content": (
                "Optimize sleep with: consistent sleep/wake times (even weekends), cool dark bedroom (16-19C), no screens 60 min before bed, caffeine cutoff 8-10h before sleep, and a wind-down routine. Athletic performance improves measurably at 8-9h of sleep: reaction time, sprint speed, and accuracy all gain. Napping 20-30 min before 3pm can supplement night sleep without disrupting it. "
            ),
                "source": "National Sleep Foundation / sports science literature",
                "relevance_keywords": ["sleep", "hygiene", "nap", "bed", "insomnia", "tired", "rest"],
            },
            {
                "topic": "DOMS and muscle soreness",
                "content": (
                "Delayed Onset Muscle Soreness (DOMS) peaks 24-72h after novel or intense exercise and is caused by microtrauma and inflammation — not lactic acid. It does NOT indicate growth and should not stop training: light movement, gentle cardio, and foam rolling increase blood flow and reduce perceived soreness. Severe soreness lasting 5+ days or with dark urine warrants medical attention (rhabdomyolysis risk). "
            ),
                "source": "sports medicine literature",
                "relevance_keywords": ["doms", "sore", "soreness", "ache", "muscle pain", "recovery"],
            },
            {
                "topic": "Cold water immersion and contrast therapy",
                "content": (
                "Cold water immersion (10-15C, 10-15 min) reduces soreness and perceived fatigue but may blunt hypertrophy when used immediately after every resistance session — it dampens the mTOR signaling response. Best use: after cardio or on rest days, or before sleep on hard training days. Contrast therapy (hot/cold alternation) is a good middle ground for general recovery and circulation. "
            ),
                "source": "Roberts et al. 2015, Journal of Physiology",
                "relevance_keywords": ["ice", "cold", "contrast", "ice bath", "cryotherapy", "sauna"],
            },
            {
                "topic": "Active recovery and light movement",
                "content": (
                "Active recovery (walking, cycling at 50-60% max HR, mobility flow, yoga) for 20-40 min on rest days accelerates lactate clearance, increases blood flow to recovering muscles, and improves next-day performance versus full inactivity. Daily step count of 7,000-10,000 also supports recovery and general health independent of training. "
            ),
                "source": "exercise recovery research",
                "relevance_keywords": ["active recovery", "walk", "yoga", "light cardio", "rest day"],
            },
            {
                "topic": "Stress and recovery balance",
                "content": (
                "Total allostatic load — training stress PLUS life stress (work, relationships, sleep debt) — determines recovery capacity. When life stress is high, reduce training volume/intensity proactively rather than forcing the plan. Subjective readiness (energy, motivation, soreness) is a validated proxy: score 1-10 daily and modulate training accordingly. "
            ),
                "source": "sports science / allostatic load literature",
                "relevance_keywords": ["stress", "burnout", "readiness", "overtraining", "fatigue"],
            },
            {
                "topic": "Massage, foam rolling and mobility tools",
                "content": (
                "Foam rolling and massage increase range of motion short-term and reduce perceived soreness, though effects on long-term performance are modest. Use 30-60 seconds per muscle group before training as part of warm-up, and 5-10 min after training. Avoid deep rolling on acute injuries or bruises. Stretching: dynamic before, static (30-60s holds) after training. "
            ),
                "source": "sports medicine consensus",
                "relevance_keywords": ["foam", "massage", "roll", "stretch", "mobility", "release"],
            },
            {
                "topic": "Tapering before events",
                "content": (
                "A taper — reducing training volume by 40-60% over 7-14 days while keeping intensity — allows performance to peak for a competition. Studies show 2-6% performance improvements with a well-executed taper. Maintain exercise frequency and intensity, drop only volume, and prioritize sleep and nutrition during the taper window. "
            ),
                "source": "Bosquet et al. 2007, Sports Medicine",
                "relevance_keywords": ["taper", "peak", "competition", "event", "race", "deload"],
            },
        ],
    },
    # Enriched entries (v2)
    "exercise_science": {
        "entries": [
            {
                "topic": "Training frequency and weekly sets",
                "content": (
                "For muscle growth, 10-20 hard sets per muscle per week is the evidence-based sweet spot. Splitting them across 2-3 sessions per muscle per week beats one mega-session: frequency 2x vs 1x yields ~10% more hypertrophy at equal volume. Beginners need fewer sets (10-12) than advanced lifters (15-20+). If you can only train 3 days/week, full-body or upper/lower splits work best. "
            ),
                "source": "Schoenfeld et al. 2016-2019 meta-analyses",
                "relevance_keywords": ["frequency", "split", "weekly", "sets", "hypertrophy", "schedule"],
            },
            {
                "topic": "Rep ranges and muscle growth",
                "content": (
                "Hypertrophy occurs across a wide rep range (5-30 reps) as long as sets are taken close to failure (0-3 reps in reserve). Heavy low-rep (1-5) builds strength and myofibrillar density; moderate (6-12) is the classic hypertrophy zone; light (15-30) builds endurance with less joint stress. Rotate rep ranges over training blocks to avoid plateaus. "
            ),
                "source": "Schoenfeld 2010 / NSCA research",
                "relevance_keywords": ["reps", "rep range", "hypertrophy", "strength", "sets", "failure"],
            },
            {
                "topic": "Rest intervals between sets",
                "content": (
                "Rest 3-5 minutes between heavy compound sets (strength focus) to fully replenish ATP-PC stores. Rest 60-90 seconds for hypertrophy work in the 6-12 rep range — sufficient metabolic stress without excessive fatigue. Rest 30-60 seconds for endurance/circuit work. Insufficient rest is the most common programming error: it caps the weight you can lift. "
            ),
                "source": "NSCA position stand",
                "relevance_keywords": ["rest", "rest time", "between sets", "interval", "break"],
            },
            {
                "topic": "Tempo and time under tension",
                "content": (
                "Tempo notation (eccentric-pause-concentric, e.g. 3-1-1) controls time under tension. A controlled 2-4 second eccentric (lowering phase) maximizes mechanical tension and microtrauma for growth. Avoid bouncing or momentum — they reduce muscle activation by up to 30%. Explosive concentric (1s) preserves power output. "
            ),
                "source": "exercise science / EMG research",
                "relevance_keywords": ["tempo", "eccentric", "negative", "slow", "form", "time under tension"],
            },
            {
                "topic": "Training to failure",
                "content": (
                "Training to absolute failure is not required for growth: stopping 1-3 reps short (RIR 1-3) produces nearly identical hypertrophy with substantially less fatigue and injury risk. Reserve true failure sets for the last set of an exercise, 1-2x per week per muscle. Frequent failure training increases systemic fatigue and can impair recovery and progress. "
            ),
                "source": "Nóbrega et al. 2018 / recent meta-analyses",
                "relevance_keywords": ["failure", "rpe", "rir", "intensity", "hard", "grind"],
            },
            {
                "topic": "Periodization models",
                "content": (
                "Linear periodization: steadily increase load, drop volume — best for beginners. Block/undulating periodization: rotate rep ranges weekly or daily — best for intermediates. Conjugate/auto-regulation: vary intensity by daily readiness — best for advanced lifters. All models work; the common thread is systematic variation and progressive overload over time. "
            ),
                "source": "periodization literature (Bompa, Zatsiorsky)",
                "relevance_keywords": ["periodization", "block", "undulating", "program", "plan", "cycle"],
            },
            {
                "topic": "Sticking points and stall busters",
                "content": (
                "Sticking points (e.g. mid-range of bench press) are where mechanical advantage is worst. Fixes: (1) pause reps at the sticking point, (2) partial-range work in the sticking zone, (3) 2-4 weeks of lighter volume to dissipate fatigue, (4) strengthen the weak link (e.g. triceps for bench, quads for squat), (5) add one back-off set at 90% of top weight. "
            ),
                "source": "strength coaching literature",
                "relevance_keywords": ["plateau", "stuck", "stall", "sticking", "no progress", "failed"],
            },
            {
                "topic": "Cardio and strength compatibility",
                "content": (
                "Concurrent training: cardio and lifting together is fine, but heavy endurance work (>5h/week) can blunt strength gains slightly. Order matters: lift first, then cardio, or separate by 6+ hours. Low-intensity steady state (LISS) interferes less than HIIT. Zone 2 cardio (2-3x/week, 30-45 min) improves recovery and work capacity without compromising gains. "
            ),
                "source": "Wilson et al. 2012 / concurrent training research",
                "relevance_keywords": ["cardio", "running", "hiit", "endurance", "concurrent", "aerobic"],
            },
        ],
    },
    # Enriched entries (v2)
    "nutrition_basics": {
        "entries": [
            {
                "topic": "Calorie deficit math",
                "content": (
                "1 kg of fat ≈ 7,700 kcal. A deficit of 300-500 kcal/day yields 0.3-0.5 kg fat loss per week — sustainable and muscle-sparing. Estimate TDEE with Mifflin-St Jeor: men 10xweight(kg)+6.25xheight(cm)-5xage+5; women 10xweight+6.25xheight-5xage-161, then multiply by activity factor 1.2-1.9. Recompute every 5 kg lost — your TDEE drops as you shrink. "
            ),
                "source": "Mifflin-St Jeor equation / sports nutrition research",
                "relevance_keywords": ["calorie", "deficit", "tdee", "cut", "fat loss", "lose weight", "diet"],
            },
            {
                "topic": "Carbohydrate timing",
                "content": (
                "Carbs fuel training: 3-5 g/kg/day for general training, 6-10 g/kg/day for high volume. Peri-workout: a 30-60g carb + 20-30g protein meal 1-2h before training improves performance; post-workout carbs (0.5-1 g/kg) replenish glycogen, especially after 2+ sessions/day. Low-carb diets work for fat loss but typically impair high-intensity performance initially. "
            ),
                "source": "ISSN sports nutrition guidelines",
                "relevance_keywords": ["carb", "carbohydrate", "glycogen", "pre workout", "post workout", "sugar"],
            },
            {
                "topic": "Creatine supplementation",
                "content": (
                "Creatine monohydrate is the most evidence-backed supplement: 3-5 g/day improves strength, power, and lean mass gains with no meaningful side effects in healthy individuals. Loading (20 g/day for 5-7 days) saturates faster but is optional. Take it any time of day, consistently. It does not cause kidney damage in healthy people — stay hydrated. "
            ),
                "source": "Kreider et al. 2017, ISSN position stand",
                "relevance_keywords": ["creatine", "supplement", "preworkout", "powder", "gains"],
            },
            {
                "topic": "Protein distribution and timing",
                "content": (
                "Muscle protein synthesis (MPS) peaks for ~4-6h after a protein-rich meal. Distribute 0.4-0.55 g/kg per meal across 3-5 meals (e.g. 80kg lifter: 32-44g per meal) to keep MPS elevated all day. The 'anabolic window' is wider than marketing claims — total daily protein matters most, though a post-workout meal within 2h is a sensible habit. "
            ),
                "source": "Schoenfeld & Aragon 2018",
                "relevance_keywords": ["protein timing", "meal", "anabolic", "post workout", "eat"],
            },
            {
                "topic": "Fat intake for hormones",
                "content": (
                "Dietary fat supports hormone production — testosterone, estrogen, and thyroid function. Keep fat at 0.6-1.0 g/kg/day (about 20-35% of calories). Very low fat diets (<15% calories) can drop testosterone and impair recovery. Prioritize unsaturated fats (olive oil, nuts, avocado, fish) while limiting trans fats and excess saturated fat. "
            ),
                "source": "sports nutrition literature",
                "relevance_keywords": ["fat", "testosterone", "hormone", "oil", "omega", "nuts"],
            },
            {
                "topic": "Body recomposition",
                "content": (
                "Body recomposition — losing fat while gaining muscle — works best for beginners, detrained lifters, and people with higher body fat. Strategy: small deficit (200-300 kcal), high protein (2.0-2.4 g/kg), train hard with progressive overload, and expect slow scale movement — track waist and strength instead. Recomp is inefficient once you're lean (<15% men, <24% women) — then bulk/cut in cycles. "
            ),
                "source": "body composition research",
                "relevance_keywords": ["recomp", "recomposition", "lean", "tone", "lose fat gain muscle"],
            },
            {
                "topic": "Fat loss plateaus",
                "content": (
                "Plateaus happen because TDEE drops with weight loss (less mass to move, hormonal adaptation, NEAT decline). Break through by: (1) re-adding steps (NEAT is the biggest variable), (2) diet breaks — 1-2 weeks at maintenance every 8-12 weeks restores leptin and adherence, (3) re-measuring portions (they creep), (4) adding protein, (5) patience — 0.25-0.5 kg/week is sustainable loss, not a stall. "
            ),
                "source": "obesity research / diet adherence literature",
                "relevance_keywords": ["plateau", "stuck", "weight loss", "stall", "deficit not working"],
            },
            {
                "topic": "Micronutrients for training",
                "content": (
                "Key micronutrients for lifters: vitamin D (2000-4000 IU/day if deficient — most are), magnesium (300-400 mg/day — supports muscle function and sleep), zinc (10-15 mg/day — testosterone support), iron (especially women — anemia kills performance), and omega-3s (1-2 g EPA/DHA — joint and inflammation support). A multivitamin is cheap insurance; food first. "
            ),
                "source": "sports nutrition consensus",
                "relevance_keywords": ["vitamin", "mineral", "magnesium", "zinc", "iron", "d", "omega"],
            },
        ],
    },
    # Enriched entries (v2)
    "injury_prevention": {
        "entries": [
            {
                "topic": "Cooldown and flexibility",
                "content": (
                "A 5-10 min cooldown (light cardio + static stretching of trained muscles, 30-60s holds) accelerates the transition back to rest, reduces next-day stiffness, and improves long-term flexibility. Stretch to mild tension, never pain. Add 2-3 sessions/week of dedicated mobility work (hips, thoracic spine, shoulders, ankles) — the areas that limit squat and overhead positions. "
            ),
                "source": "flexibility training research",
                "relevance_keywords": ["cooldown", "cool down", "stretch", "flexibility", "mobility"],
            },
            {
                "topic": "Prehab for common injuries",
                "content": (
                "Prehab = training to prevent injuries. Highest-value prehab work: rotator cuff (external rotation, face pulls) for shoulders; glute medius + tibialis raises for knees; core bracing + hip hinge patterns for lower back; grip work for elbows. 2-3 sets, 2-3x/week, light weight, perfect form. Prehab beats rehab every time. "
            ),
                "source": "sports physiotherapy literature",
                "relevance_keywords": ["prehab", "rotator", "shoulder", "knee", "back", "prevent injury"],
            },
            {
                "topic": "Knee pain management",
                "content": (
                "Anterior knee pain (runners knee / patellofemoral) is usually a load management issue, not a structural one. Fixes: reduce jump/run volume temporarily, strengthen quads (leg extensions, step-downs) and glute medius, check footwear, avoid deep knee valgus in squats. Pain under 3/10 that settles within 24h is manageable; sharp pain or swelling needs professional assessment. "
            ),
                "source": "sports physio consensus",
                "relevance_keywords": ["knee", "runner knee", "patella", "squat pain", "joint"],
            },
            {
                "topic": "Lower back safety",
                "content": (
                "Most lower back pain in lifters is mechanical, not structural. Principles: maintain neutral spine under load (bracing: 360-degree core tension), progress deadlift/squat loads slowly, strengthen the posterior chain (glutes, hamstrings, erectors), and get up from sitting regularly. If you feel radiating leg pain, numbness, or weakness — stop lifting and see a professional (possible disc involvement). "
            ),
                "source": "spinal health / strength coaching research",
                "relevance_keywords": ["back", "spine", "deadlift", "hernia", "disc", "sciatica", "lower back"],
            },
            {
                "topic": "Return to training after injury",
                "content": (
                "Return to training progressively: start at 50-60% of previous load, add 10% per week, and monitor pain (must stay <3/10 during and <4/10 for 24h after). Pain-free range of motion first, then load. Keep training the uninjured side (cross-education preserves up to 50% of strength). Full recovery typically takes 2-3x longer than people expect — patience prevents re-injury. "
            ),
                "source": "rehabilitation science",
                "relevance_keywords": ["rehab", "recovery from injury", "return", "re-injury", "heal"],
            },
            {
                "topic": "Overuse and tendon health",
                "content": (
                "Tendons adapt 2-4x slower than muscle — that's why tendon pain (elbow, Achilles, patellar) appears after rapid load jumps. Tendon training: isometric holds (30-45s, 70-80% max) daily for pain management, then slow heavy eccentrics (3-5s lowering) 2-3x/week. Avoid pain >4/10 during tendon work. Gradual load progression is the real cure. "
            ),
                "source": "tendinopathy research (Malliaras et al.)",
                "relevance_keywords": ["tendon", "tendinitis", "elbow", "achilles", "patellar", "jumper knee"],
            },
        ],
    },
    # Enriched entries (v2)
    "mental_health": {
        "entries": [
            {
                "topic": "Habit formation for consistency",
                "content": (
                "Consistency beats motivation: attach training to an existing cue (e.g. 'after morning coffee'), start embarrassingly small (10 min), and never miss twice in a row. Identity framing ('I am a person who trains') outperforms outcome goals ('I want abs'). Track streaks — a visible streak is a powerful behavioral anchor. It takes ~66 days for a habit to automate. "
            ),
                "source": "Lally et al. 2010 / habit research",
                "relevance_keywords": ["habit", "consistency", "streak", "routine", "discipline", "motivation"],
            },
            {
                "topic": "Gym anxiety and social barriers",
                "content": (
                "Gym anxiety is common (up to 50% of beginners) and fades with exposure. Strategies: go at off-peak hours initially, bring a plan (a written workout removes decision anxiety), use headphones as a social shield, start with machines (less skill pressure), and remember: experienced lifters are focused on themselves, not judging you. Every session completed is exposure therapy working. "
            ),
                "source": "exercise psychology literature",
                "relevance_keywords": ["anxiety", "nervous", "gym", "embarrassed", "social", "beginner", "scared"],
            },
            {
                "topic": "Goal setting that works",
                "content": (
                "Use SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound. Better: process goals beat outcome goals — 'train 4x this week' beats 'lose 10kg'. Set 3 tiers: 90-day outcome, 30-day milestone, weekly process targets. Review weekly and adjust — goals are a compass, not a contract. Celebrate process wins (showing up) as much as outcomes. "
            ),
                "source": "goal-setting theory (Locke & Latham)",
                "relevance_keywords": ["goal", "smart", "target", "plan", "achieve", "milestone"],
            },
            {
                "topic": "Stress management through training",
                "content": (
                "Training is a stress inoculation tool: 30-45 min of moderate exercise lowers cortisol acutely and improves mood for hours after. Pair training with breathing (4-4-4 box breathing), nature exposure, and screen-free downtime for compounding stress relief. Overtraining is itself a stressor — if training feels like a chore for 2+ weeks, deload and reassess, don't push through. "
            ),
                "source": "exercise psychology / stress research",
                "relevance_keywords": ["stress", "anxiety", "cortisol", "burnout", "overwhelmed", "relax"],
            },
            {
                "topic": "Exercise addiction and healthy balance",
                "content": (
                "Exercise can become compulsive: training through injury, guilt when missing sessions, prioritizing training over relationships/work, or extreme restriction. Healthy signs: you can skip a session without distress, rest days feel earned not wasted, and training enhances life rather than dominating it. If training feels like a compulsion, talk to a professional — movement should serve you, not rule you. "
            ),
                "source": "exercise psychology literature",
                "relevance_keywords": ["addiction", "compulsive", "guilt", "overtraining", "obsessive", "balance"],
            },
            {
                "topic": "Body image and training mindset",
                "content": (
                "Train for function and feeling, not just appearance — performance improvements (strength, endurance, energy) are more durable motivators than mirror checks. Compare yourself to last month's you, not to edited social media. Progress photos every 4 weeks + strength numbers beat daily scale anxiety. If body dissatisfaction is severe or eating-disordered thoughts appear, seek professional support. "
            ),
                "source": "body image research",
                "relevance_keywords": ["body image", "confidence", "mirror", "appearance", "self esteem", "compare"],
            },
        ],
    },
}

class RAGKnowledgeRetriever:
    """
    Retrieval-Augmented Generation system for fitness knowledge.
    Uses keyword matching and relevance scoring to retrieve contextual knowledge.
    """

    def __init__(self):
        self.knowledge_base = FITNESS_KNOWLEDGE
        # Merge enriched entries, deduping by topic
        for category, data in EXTRA_KNOWLEDGE.items():
            existing = {e.get("topic") for e in self.knowledge_base.get(category, {}).get("entries", [])}
            for entry in data.get("entries", []):
                if entry.get("topic") not in existing:
                    self.knowledge_base.setdefault(category, {"entries": []})["entries"].append(entry)
        self._flat_entries: List[Dict[str, Any]] = []
        for category, data in self.knowledge_base.items():
            for entry in data.get("entries", []):
                entry["category"] = category
                self._flat_entries.append(entry)

    def retrieve(
        self, query: str, top_k: int = 3, category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant knowledge entries for a query.
        Uses TF-IDF-like keyword scoring.
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        scored = []
        for entry in self._flat_entries:
            if category_filter and entry.get("category") != category_filter:
                continue

            score = 0.0
            keywords = entry.get("relevance_keywords", [])
            topic = entry.get("topic", "").lower()

            # Keyword match scoring
            for kw in keywords:
                if kw in query_lower:
                    score += 3.0
                elif any(w in kw for w in query_words if len(w) > 2):
                    score += 1.0

            # Topic match
            topic_words = set(re.findall(r'\w+', topic))
            overlap = query_words & topic_words
            score += len(overlap) * 2.0

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:top_k]]

    def build_context_string(self, query: str, max_tokens: int = 800) -> str:
        """Build a context string for LLM injection from retrieved knowledge."""
        entries = self.retrieve(query, top_k=3)
        if not entries:
            return ""

        context_parts = ["RELEVANT FITNESS KNOWLEDGE:"]
        token_count = 0

        for entry in entries:
            content = entry.get("content", "")
            # Rough token estimate (1 token ≈ 4 chars)
            entry_tokens = len(content) // 4
            if token_count + entry_tokens > max_tokens:
                break

            source = entry.get("source", "")
            topic = entry.get("topic", "")
            context_parts.append(f"\n[{topic}] ({source})\n{content}")
            token_count += entry_tokens

        return "\n".join(context_parts)

    def get_related_topics(self, topic: str, limit: int = 3) -> List[str]:
        """Suggest related topics based on category overlap."""
        found = []
        topic_lower = topic.lower()

        for category, data in self.knowledge_base.items():
            for entry in data.get("entries", []):
                if entry.get("topic", "").lower() != topic_lower:
                    keywords = entry.get("relevance_keywords", [])
                    if any(kw in topic_lower for kw in keywords):
                        found.append(entry.get("topic", ""))
                        if len(found) >= limit:
                            return found
        return found

    def get_status(self) -> Dict[str, Any]:
        total = len(self._flat_entries)
        categories = len(self.knowledge_base)
        return {
            "total_entries": total,
            "categories": categories,
            "category_names": list(self.knowledge_base.keys()),
        }


rag_retriever = RAGKnowledgeRetriever()
