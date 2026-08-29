"""
Content Platform Service — YouTube-like Health Video/GIF Feed

Features:
- Exercise demonstration video/GIF library (categorized)
- Health knowledge articles and tips
- Personalized content feed based on user goals/conditions
- Content bookmarking and favorites
- Trending health content
- Expert health tips (curated knowledge base)
- Workout tutorial playlists
- Nutrition education content
- Mental health awareness content
- Content engagement tracking

Inspired by: YouTube health channels, Peloton content, Nike Training Club
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ContentType(Enum):
    EXERCISE_VIDEO = "exercise_video"
    EXERCISE_GIF = "exercise_gif"
    WORKOUT_TUTORIAL = "workout_tutorial"
    NUTRITION_TIP = "nutrition_tip"
    MENTAL_HEALTH = "mental_health"
    SLEEP_EDUCATION = "sleep_education"
    INJURY_PREVENTION = "injury_prevention"
    RECOVERY_GUIDE = "recovery_guide"
    STRETCHING = "stretching"
    MEDITATION = "meditation"
    HEALTH_KNOWLEDGE = "health_knowledge"
    MOTIVATIONAL = "motivational"
    RECIPE = "recipe"
    EXERCISE_FORM = "exercise_form"


class ContentDifficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class ContentCategory(Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    RECOVERY = "recovery"
    NUTRITION = "nutrition"
    SLEEP = "sleep"
    MENTAL_WELLNESS = "mental_wellness"
    GENERAL_HEALTH = "general_health"
    BEGINNER_GUIDE = "beginner_guide"


@dataclass
class ContentItem:
    id: str
    title: str
    description: str
    content_type: ContentType
    category: ContentCategory
    difficulty: ContentDifficulty
    duration_seconds: Optional[int]
    thumbnail_url: str
    media_url: str  # video or GIF URL
    tags: list[str]
    muscles_targeted: list[str]
    equipment_needed: list[str]
    view_count: int = 0
    like_count: int = 0
    bookmark_count: int = 0
    rating: float = 4.5
    source: str = "adapfit"
    author: str = "AdapFit Team"
    created_at: float = field(default_factory=time.time)


@dataclass
class ContentFeed:
    items: list[ContentItem]
    total_count: int
    page: int
    page_size: int
    category: Optional[str]
    content_type: Optional[str]


@dataclass
class UserEngagement:
    content_id: str
    viewed: bool = False
    bookmarked: bool = False
    liked: bool = False
    completed: bool = False
    watch_time_seconds: int = 0
    rating: Optional[float] = None


class ContentPlatformService:
    """
    YouTube-like health content platform.
    
    Provides curated health, fitness, and wellness content:
    - Exercise demonstration GIFs and videos
    - Workout tutorials
    - Nutrition education
    - Mental health resources
    - Sleep education
    - Personalized recommendations based on user profile
    """

    def __init__(self):
        self._content_library = self._init_content_library()
        self._user_engagement: dict[str, list[UserEngagement]] = {}
        self._bookmarks: dict[str, list[str]] = {}

    def get_content_feed(self, user_id: str = "default", category: Optional[str] = None,
                        content_type: Optional[str] = None, page: int = 1,
                        page_size: int = 20, difficulty: Optional[str] = None) -> ContentFeed:
        """Get personalized content feed."""
        items = self._content_library.copy()
        
        # Filter by category
        if category:
            items = [i for i in items if i.category.value == category]
        
        # Filter by content type
        if content_type:
            items = [i for i in items if i.content_type.value == content_type]
        
        # Filter by difficulty
        if difficulty:
            items = [i for i in items if i.difficulty.value == difficulty or i.difficulty == ContentDifficulty.ALL_LEVELS]
        
        # Sort by relevance (rating + views)
        items.sort(key=lambda x: x.rating * 0.6 + min(x.view_count / 1000, 10) * 0.4, reverse=True)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        
        return ContentFeed(
            items=items[start:end],
            total_count=len(items),
            page=page,
            page_size=page_size,
            category=category,
            content_type=content_type,
        )

    def get_content_by_id(self, content_id: str) -> Optional[dict]:
        """Get detailed content item."""
        for item in self._content_library:
            if item.id == content_id:
                item.view_count += 1
                return {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "content_type": item.content_type.value,
                    "category": item.category.value,
                    "difficulty": item.difficulty.value,
                    "duration_seconds": item.duration_seconds,
                    "thumbnail_url": item.thumbnail_url,
                    "media_url": item.media_url,
                    "tags": item.tags,
                    "muscles_targeted": item.muscles_targeted,
                    "equipment_needed": item.equipment_needed,
                    "view_count": item.view_count,
                    "like_count": item.like_count,
                    "rating": item.rating,
                    "author": item.author,
                    "related_content": self._get_related(item),
                }
        return None

    def search_content(self, query: str, limit: int = 20) -> list[dict]:
        """Search content by keyword."""
        query_lower = query.lower()
        results = []
        
        for item in self._content_library:
            score = 0
            if query_lower in item.title.lower():
                score += 10
            if query_lower in item.description.lower():
                score += 5
            if any(query_lower in tag.lower() for tag in item.tags):
                score += 7
            if any(query_lower in m.lower() for m in item.muscles_targeted):
                score += 6
            
            if score > 0:
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type.value,
                    "category": item.category.value,
                    "difficulty": item.difficulty.value,
                    "relevance_score": score,
                    "thumbnail_url": item.thumbnail_url,
                    "duration_seconds": item.duration_seconds,
                    "rating": item.rating,
                })
        
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    def get_trending(self, limit: int = 20) -> list[dict]:
        """Get trending content."""
        sorted_content = sorted(
            self._content_library,
            key=lambda x: x.view_count + x.like_count * 5,
            reverse=True,
        )
        
        return [
            {
                "id": item.id,
                "title": item.title,
                "content_type": item.content_type.value,
                "category": item.category.value,
                "thumbnail_url": item.thumbnail_url,
                "view_count": item.view_count,
                "rating": item.rating,
                "trending_score": item.view_count + item.like_count * 5,
            }
            for item in sorted_content[:limit]
        ]

    def get_workout_playlist(self, workout_type: str, level: str = "all_levels") -> dict:
        """Get a curated workout playlist."""
        playlists = {
            "full_body": {
                "title": "Full Body Workout Tutorial",
                "description": "Complete guide to full body training with proper form",
                "total_duration_minutes": 45,
                "exercises": ["squat", "bench_press", "deadlift", "overhead_press", "barbell_row", "pull_up"],
            },
            "home_no_equipment": {
                "title": "Home Workout — No Equipment Needed",
                "description": "Effective bodyweight exercises you can do anywhere",
                "total_duration_minutes": 30,
                "exercises": ["push_up", "bodyweight_squat", "plank", "burpee", "mountain_climber", "lunges"],
            },
            "stretching_recovery": {
                "title": "Post-Workout Stretching & Recovery",
                "description": "Essential stretches for faster recovery",
                "total_duration_minutes": 20,
                "exercises": ["hamstring_stretch", "quad_stretch", "hip_flexor", "chest_stretch", "shoulder_stretch", "foam_rolling"],
            },
            "core_strength": {
                "title": "Core Strength Foundation",
                "description": "Build a strong core for better performance",
                "total_duration_minutes": 25,
                "exercises": ["plank", "dead_bug", "bird_dog", "russian_twist", "hollow_body", "leg_raise"],
            },
            "beginner_fitness": {
                "title": "Your First Workout — Beginner's Guide",
                "description": "Start your fitness journey with proper fundamentals",
                "total_duration_minutes": 30,
                "exercises": ["bodyweight_squat", "wall_push_up", "glute_bridge", "step_up", "band_pull_apart", "bird_dog"],
            },
        }
        
        playlist = playlists.get(workout_type, playlists["full_body"])
        playlist["workout_type"] = workout_type
        playlist["level"] = level
        playlist["items"] = [
            item for item in self._content_library
            if item.content_type in (ContentType.EXERCISE_GIF, ContentType.EXERCISE_VIDEO, ContentType.EXERCISE_FORM)
        ][:6]
        
        return playlist

    def get_health_knowledge(self, topic: Optional[str] = None) -> list[dict]:
        """Get health knowledge articles and tips."""
        knowledge = [
            {
                "id": "hk_001",
                "title": "Understanding Your Heart Rate Zones",
                "summary": "Learn how different heart rate zones affect your training and recovery",
                "category": "heart_health",
                "read_time_minutes": 5,
                "key_points": [
                    "Zone 1 (50-60% max HR): Warm-up and recovery",
                    "Zone 2 (60-70%): Fat burning and endurance base",
                    "Zone 3 (70-80%): Aerobic fitness improvement",
                    "Zone 4 (80-90%): Anaerobic threshold training",
                    "Zone 5 (90-100%): Maximum effort, VO2max improvement",
                ],
            },
            {
                "id": "hk_002",
                "title": "Sleep and Recovery: The Science",
                "summary": "Why 7-9 hours of quality sleep is crucial for fitness",
                "category": "sleep",
                "read_time_minutes": 7,
                "key_points": [
                    "Growth hormone is primarily released during deep sleep",
                    "REM sleep consolidates motor learning (exercise form)",
                    "Sleep debt impairs recovery by up to 40%",
                    "Consistent sleep schedule improves HRV by 10-15%",
                    "Screen time before bed reduces sleep quality by 25%",
                ],
            },
            {
                "id": "hk_003",
                "title": "Nutrition Timing for Performance",
                "summary": "When and what to eat around workouts for optimal results",
                "category": "nutrition",
                "read_time_minutes": 6,
                "key_points": [
                    "Pre-workout: Carbs + protein 2-3 hours before",
                    "During workout: Water + electrolytes for sessions > 60min",
                    "Post-workout: 20-40g protein within 2 hours",
                    "Daily protein: 1.6-2.2g per kg bodyweight for muscle building",
                    "Hydration: Minimum 35ml per kg bodyweight daily",
                ],
            },
            {
                "id": "hk_004",
                "title": "Stress and Cortisol: What You Need to Know",
                "summary": "How chronic stress affects fitness and health",
                "category": "mental_health",
                "read_time_minutes": 5,
                "key_points": [
                    "Chronic cortisol elevation promotes belly fat storage",
                    "Stress reduces testosterone and growth hormone",
                    "Meditation lowers cortisol by 23% on average",
                    "Exercise is one of the best stress management tools",
                    "Social connection buffers stress response",
                ],
            },
            {
                "id": "hk_005",
                "title": "HRV: Your Body's Recovery Dashboard",
                "summary": "Heart Rate Variability explains why some days feel harder",
                "category": "heart_health",
                "read_time_minutes": 8,
                "key_points": [
                    "Higher HRV = Better recovery and parasympathetic tone",
                    "RMSSD is the most reliable HRV metric for fitness",
                    "Alcohol reduces HRV by 20-40% for 24+ hours",
                    "Consistent training improves baseline HRV over time",
                    "Morning HRV is the best indicator of daily readiness",
                ],
            },
            {
                "id": "hk_006",
                "title": "Injury Prevention: Warm-Up Science",
                "summary": "Evidence-based warm-up protocols to prevent injury",
                "category": "injury_prevention",
                "read_time_minutes": 4,
                "key_points": [
                    "Dynamic stretching before exercise reduces injury by 35%",
                    "Gradual intensity increase over 5-10 minutes",
                    "Specific warm-up for the muscle groups being trained",
                    "Cold muscles are 20% less elastic — warm up first",
                    "Post-workout static stretching improves flexibility",
                ],
            },
            {
                "id": "hk_007",
                "title": "The Truth About Supplements",
                "summary": "Evidence-based guide to fitness supplements",
                "category": "nutrition",
                "read_time_minutes": 6,
                "key_points": [
                    "Creatine monohydrate: Most studied, safe, effective (3-5g/day)",
                    "Protein powder: Convenient way to hit protein goals",
                    "Caffeine: 3-6mg/kg improves performance 3-5%",
                    "Vitamin D: Deficiency common, impacts recovery",
                    "Omega-3: Anti-inflammatory, supports recovery",
                ],
            },
            {
                "id": "hk_008",
                "title": "Digital Wellness & Screen Time",
                "summary": "How your phone habits affect your health",
                "category": "general_health",
                "read_time_minutes": 5,
                "key_points": [
                    "Blue light suppresses melatonin production by 50%",
                    "Phone use within 1hr of bed delays sleep onset by 30min",
                    "Social media comparison increases anxiety by 27%",
                    "Digital detox for 3 days improves mood by 25%",
                    "Mindful phone use correlates with better sleep quality",
                ],
            },
        ]
        
        if topic:
            knowledge = [k for k in knowledge if topic.lower() in k["category"].lower() or topic.lower() in k["title"].lower()]
        
        return knowledge

    def bookmark_content(self, user_id: str, content_id: str) -> dict:
        """Bookmark a content item."""
        if user_id not in self._bookmarks:
            self._bookmarks[user_id] = []
        
        if content_id not in self._bookmarks[user_id]:
            self._bookmarks[user_id].append(content_id)
            # Update content item bookmark count
            for item in self._content_library:
                if item.id == content_id:
                    item.bookmark_count += 1
                    break
        
        return {"bookmarked": True, "total_bookmarks": len(self._bookmarks.get(user_id, []))}

    def get_user_bookmarks(self, user_id: str) -> list[dict]:
        """Get user's bookmarked content."""
        bookmark_ids = self._bookmarks.get(user_id, [])
        return [
            {
                "id": item.id,
                "title": item.title,
                "content_type": item.content_type.value,
                "category": item.category.value,
                "thumbnail_url": item.thumbnail_url,
            }
            for item in self._content_library if item.id in bookmark_ids
        ]

    def get_personalized_recommendations(self, user_goals: list[str], fitness_level: str,
                                         health_conditions: list[str]) -> list[dict]:
        """Get personalized content recommendations."""
        recommended = []
        
        for item in self._content_library:
            score = 0
            
            # Match goals to categories
            goal_category_map = {
                "weight_loss": ["cardio", "nutrition"],
                "muscle_gain": ["strength"],
                "flexibility": ["flexibility"],
                "stress_relief": ["mental_wellness", "recovery"],
                "better_sleep": ["sleep"],
                "general_fitness": ["general_health", "cardio", "strength"],
            }
            
            for goal in user_goals:
                matching_cats = goal_category_map.get(goal, [])
                if item.category.value in matching_cats:
                    score += 5
            
            # Match difficulty
            if fitness_level == "beginner" and item.difficulty in (ContentDifficulty.BEGINNER, ContentDifficulty.ALL_LEVELS):
                score += 3
            elif fitness_level == "intermediate" and item.difficulty in (ContentDifficulty.INTERMEDIATE, ContentDifficulty.ALL_LEVELS):
                score += 3
            elif fitness_level == "advanced":
                score += 3
            
            # Health condition relevance
            for condition in health_conditions:
                if any(cond in item.tags for cond in [condition, "recovery", "gentle"]):
                    score += 4
            
            if score > 0:
                recommended.append({
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type.value,
                    "category": item.category.value,
                    "thumbnail_url": item.thumbnail_url,
                    "relevance_score": score,
                    "duration_seconds": item.duration_seconds,
                })
        
        recommended.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommended[:20]

    def track_engagement(self, user_id: str, content_id: str, action: str) -> dict:
        """Track user engagement with content."""
        if user_id not in self._user_engagement:
            self._user_engagement[user_id] = []
        
        engagement = next(
            (e for e in self._user_engagement[user_id] if e.content_id == content_id),
            None,
        )
        
        if not engagement:
            engagement = UserEngagement(content_id=content_id)
            self._user_engagement[user_id].append(engagement)
        
        if action == "view":
            engagement.viewed = True
        elif action == "bookmark":
            engagement.bookmarked = True
        elif action == "like":
            engagement.liked = True
        elif action == "complete":
            engagement.completed = True
        
        return {"tracked": True, "action": action, "content_id": content_id}

    # === Private helpers ===

    def _get_related(self, item: ContentItem) -> list[dict]:
        """Get related content items."""
        related = []
        for other in self._content_library:
            if other.id != item.id and other.category == item.category:
                related.append({
                    "id": other.id,
                    "title": other.title,
                    "content_type": other.content_type.value,
                    "thumbnail_url": other.thumbnail_url,
                })
            if len(related) >= 4:
                break
        return related

    def _init_content_library(self) -> list[ContentItem]:
        """Initialize with comprehensive health content library."""
        content = []
        idx = 0
        
        # Exercise GIFs - Strength
        strength_exercises = [
            ("Barbell Back Squat", "compound", "legs", ["quads", "glutes", "core"], "barbell"),
            ("Bench Press", "compound", "chest", ["chest", "triceps", "front_delts"], "barbell"),
            ("Deadlift", "compound", "full_body", ["back", "glutes", "hamstrings"], "barbell"),
            ("Overhead Press", "compound", "shoulders", ["shoulders", "triceps"], "barbell"),
            ("Barbell Row", "compound", "back", ["lats", "rhomboids", "biceps"], "barbell"),
            ("Pull-Up", "compound", "back", ["lats", "biceps"], "pull_up_bar"),
            ("Dumbbell Lateral Raise", "isolation", "shoulders", ["side_delts"], "dumbbells"),
            ("Bicep Curl", "isolation", "arms", ["biceps"], "dumbbells"),
            ("Tricep Dip", "compound", "arms", ["triceps", "chest"], "parallel_bars"),
            ("Leg Press", "compound", "legs", ["quads", "glutes"], "leg_press_machine"),
            ("Romanian Deadlift", "compound", "legs", ["hamstrings", "glutes"], "barbell"),
            ("Bulgarian Split Squat", "compound", "legs", ["quads", "glutes"], "dumbbells"),
        ]
        
        for name, subtype, cat, muscles, equip in strength_exercises:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=f"{name} — Proper Form Guide",
                description=f"Learn proper {name.lower()} form with step-by-step instructions and common mistakes to avoid.",
                content_type=ContentType.EXERCISE_GIF,
                category=ContentCategory.STRENGTH,
                difficulty=ContentDifficulty.ALL_LEVELS,
                duration_seconds=30,
                thumbnail_url=f"/thumbnails/{name.lower().replace(' ', '_')}.jpg",
                media_url=f"/gifs/{name.lower().replace(' ', '_')}.gif",
                tags=[subtype, "form", "strength"],
                muscles_targeted=muscles,
                equipment_needed=[equip],
                view_count=1000 + idx * 100,
                rating=4.5 + (idx % 5) * 0.1,
            ))
            idx += 1
        
        # Cardio exercises
        cardio_exercises = [
            ("Jumping Jacks", "cardio", "full_body", []),
            ("Burpees", "cardio", "full_body", []),
            ("Mountain Climbers", "cardio", "core", []),
            ("High Knees", "cardio", "legs", []),
            ("Box Jumps", "plyometric", "legs", ["plyo_box"]),
            ("Battle Ropes", "cardio", "full_body", ["battle_ropes"]),
            ("Rowing Machine", "cardio", "full_body", ["rowing_machine"]),
            ("Jump Rope", "cardio", "full_body", ["jump_rope"]),
        ]
        
        for name, subtype, cat, equip in cardio_exercises:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=f"{name} — Cardio Blast",
                description=f"High-energy {name.lower()} tutorial for cardiovascular fitness.",
                content_type=ContentType.EXERCISE_GIF,
                category=ContentCategory.CARDIO,
                difficulty=ContentDifficulty.INTERMEDIATE,
                duration_seconds=20,
                thumbnail_url=f"/thumbnails/{name.lower().replace(' ', '_')}.jpg",
                media_url=f"/gifs/{name.lower().replace(' ', '_')}.gif",
                tags=[subtype, "cardio", "fat_burn"],
                muscles_targeted=[cat],
                equipment_needed=equip if equip else ["none"],
                view_count=800 + idx * 80,
                rating=4.4,
            ))
            idx += 1
        
        # Flexibility & Stretching
        stretches = [
            "Hamstring Stretch", "Quad Stretch", "Hip Flexor Stretch",
            "Chest Doorway Stretch", "Shoulder Cross-Body Stretch",
            "Cat-Cow Stretch", "Pigeon Pose", "Child's Pose",
            "Butterfly Stretch", "Calf Stretch",
        ]
        
        for name in stretches:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=f"{name} — Flexibility Guide",
                description=f"Proper {name.lower()} technique for improved flexibility and recovery.",
                content_type=ContentType.STRETCHING,
                category=ContentCategory.FLEXIBILITY,
                difficulty=ContentDifficulty.BEGINNER,
                duration_seconds=30,
                thumbnail_url=f"/thumbnails/{name.lower().replace(' ', '_')}.jpg",
                media_url=f"/gifs/{name.lower().replace(' ', '_')}.gif",
                tags=["stretching", "flexibility", "recovery"],
                muscles_targeted=[name.split()[0].lower()],
                equipment_needed=["none"],
                view_count=600 + idx * 50,
                rating=4.3,
            ))
            idx += 1
        
        # Mental health & meditation content
        mental_content = [
            ("5-Minute Morning Meditation", "Start your day with clarity and focus"),
            ("Guided Body Scan for Sleep", "Release tension and drift into deep sleep"),
            ("Box Breathing for Stress", "Navy SEAL technique for instant calm"),
            ("Gratitude Journaling Guide", "Science-backed mood improvement in 5 minutes"),
            ("Progressive Muscle Relaxation", "Systematically release physical tension"),
            ("Mindful Walking Meditation", "Turn your daily walk into a mindfulness practice"),
        ]
        
        for title, desc in mental_content:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=title,
                description=desc,
                content_type=ContentType.MEDITATION,
                category=ContentCategory.MENTAL_WELLNESS,
                difficulty=ContentDifficulty.BEGINNER,
                duration_seconds=300,
                thumbnail_url=f"/thumbnails/{title.lower().replace(' ', '_')}.jpg",
                media_url=f"/audio/{title.lower().replace(' ', '_')}.mp3",
                tags=["meditation", "mental_health", "stress", "sleep"],
                muscles_targeted=[],
                equipment_needed=["none"],
                view_count=500 + idx * 60,
                rating=4.7,
            ))
            idx += 1
        
        # Nutrition content
        nutrition_content = [
            ("Pre-Workout Nutrition Guide", "What to eat 2-3 hours before training"),
            ("Post-Workout Recovery Meal", "Optimal protein and carb timing"),
            ("High Protein Meal Prep", "7-day meal prep for muscle building"),
            ("Hydration Science", "How much water you really need"),
            ("Anti-Inflammatory Foods", "Eat to recover faster"),
            ("Sleep-Promoting Foods", "Foods that improve sleep quality"),
        ]
        
        for title, desc in nutrition_content:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=title,
                description=desc,
                content_type=ContentType.NUTRITION_TIP,
                category=ContentCategory.NUTRITION,
                difficulty=ContentDifficulty.BEGINNER,
                duration_seconds=180,
                thumbnail_url=f"/thumbnails/{title.lower().replace(' ', '_')}.jpg",
                media_url=f"/articles/{title.lower().replace(' ', '_')}.html",
                tags=["nutrition", "diet", "meal_planning"],
                muscles_targeted=[],
                equipment_needed=["none"],
                view_count=400 + idx * 40,
                rating=4.4,
            ))
            idx += 1
        
        # Sleep education
        sleep_content = [
            ("Sleep Architecture Explained", "Understanding sleep cycles and stages"),
            ("Blue Light & Sleep", "How screens affect your melatonin"),
            ("Optimal Sleep Environment", "Temperature, noise, and light settings"),
            ("Sleep Hygiene Checklist", "10 habits for better sleep tonight"),
        ]
        
        for title, desc in sleep_content:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=title,
                description=desc,
                content_type=ContentType.SLEEP_EDUCATION,
                category=ContentCategory.SLEEP,
                difficulty=ContentDifficulty.BEGINNER,
                duration_seconds=240,
                thumbnail_url=f"/thumbnails/{title.lower().replace(' ', '_')}.jpg",
                media_url=f"/articles/{title.lower().replace(' ', '_')}.html",
                tags=["sleep", "recovery", "wellness"],
                muscles_targeted=[],
                equipment_needed=["none"],
                view_count=300 + idx * 30,
                rating=4.6,
            ))
            idx += 1
        
        # Injury prevention
        injury_content = [
            ("Common Squat Mistakes", "Avoid these form errors to prevent knee injury"),
            ("Shoulder Health for Pressing", "Keep your shoulders healthy with proper technique"),
            ("Lower Back Protection", "Core bracing and neutral spine fundamentals"),
            ("Warm-Up Science", "Evidence-based warm-up protocols"),
        ]
        
        for title, desc in injury_content:
            content.append(ContentItem(
                id=f"ex_{idx:04d}",
                title=title,
                description=desc,
                content_type=ContentType.INJURY_PREVENTION,
                category=ContentCategory.INJURY_PREVENTION if hasattr(ContentCategory, 'INJURY_PREVENTION') else ContentCategory.GENERAL_HEALTH,
                difficulty=ContentDifficulty.BEGINNER,
                duration_seconds=200,
                thumbnail_url=f"/thumbnails/{title.lower().replace(' ', '_')}.jpg",
                media_url=f"/gifs/{title.lower().replace(' ', '_')}.gif",
                tags=["injury_prevention", "form", "safety"],
                muscles_targeted=["core", "shoulders", "back"],
                equipment_needed=["none"],
                view_count=350 + idx * 35,
                rating=4.5,
            ))
            idx += 1
        
        return content


# Singleton
content_platform_service = ContentPlatformService()
