"""Tests for Gamification Service."""
import pytest
from datetime import datetime, timedelta
from app.services.gamification import (
    Achievement, AchievementProgress, AchievementRarity, LeaderboardEntry,
    LeaderboardPeriod, PointTransaction, UserStreak,
    calculate_level_progress, calculate_points, calculate_leaderboard_ranks,
    calculate_weekly_leaderboard, update_streak, calculate_streak_multiplier,
    calculate_total_points, calculate_user_level, generate_achievement_summary,
    RARITY_MULTIPLIER,
)


def make_achievement(key="test", rarity=AchievementRarity.COMMON, points=100, max_level=3):
    return Achievement(
        key=key, name=f"Test {key}", description="Desc",
        rarity=rarity, icon="🏆", points=points, max_level=max_level,
        target_per_level=[10, 25, 50],
    )


def make_progress(key="test", value=0.0, level=0):
    return AchievementProgress(achievement_key=key, user_id="u1", current_level=level, current_value=value)


class TestLevelProgress:
    def test_no_level_up(self):
        level, progress = calculate_level_progress(5, [10, 25, 50], 0)
        assert level == 0
        assert progress == 0.5

    def test_one_level_up(self):
        level, progress = calculate_level_progress(15, [10, 25, 50], 0)
        assert level == 1
        assert progress == 0.2

    def test_multiple_level_ups(self):
        level, progress = calculate_level_progress(40, [10, 25, 50], 0)
        assert level == 2

    def test_max_level(self):
        level, progress = calculate_level_progress(200, [10, 25, 50], 0)
        assert level == 3


class TestPoints:
    def test_basic_points(self):
        ach = make_achievement(points=100, rarity=AchievementRarity.COMMON)
        prog = make_progress(level=0)
        assert calculate_points(ach, prog) == 100

    def test_rarity_multiplier(self):
        ach = make_achievement(points=100, rarity=AchievementRarity.LEGENDARY)
        prog = make_progress(level=0)
        assert calculate_points(ach, prog) == 500

    def test_level_bonus(self):
        ach = make_achievement(points=100, rarity=AchievementRarity.COMMON)
        prog = make_progress(level=2)
        assert calculate_points(ach, prog) > 100

    def test_bonus_multiplier(self):
        ach = make_achievement(points=100, rarity=AchievementRarity.COMMON)
        prog = make_progress(level=0)
        assert calculate_points(ach, prog, bonus_multiplier=2.0) == 200


class TestLeaderboard:
    def test_ranking(self):
        entries = [
            LeaderboardEntry(user_id="a", username="a", score=50),
            LeaderboardEntry(user_id="b", username="b", score=100),
            LeaderboardEntry(user_id="c", username="c", score=75),
        ]
        ranked = calculate_leaderboard_ranks(entries)
        assert ranked[0].user_id == "b"
        assert ranked[0].rank == 1
        assert ranked[1].user_id == "c"
        assert ranked[2].user_id == "a"

    def test_tie_breaking(self):
        entries = [
            LeaderboardEntry(user_id="b", username="b", score=100),
            LeaderboardEntry(user_id="a", username="a", score=100),
        ]
        ranked = calculate_leaderboard_ranks(entries)
        assert ranked[0].user_id == "a"

    def test_rank_change(self):
        entries = [
            LeaderboardEntry(user_id="b", username="b", score=100, previous_rank=2),
            LeaderboardEntry(user_id="a", username="a", score=100, previous_rank=1),
        ]
        ranked = calculate_leaderboard_ranks(entries)
        assert ranked[0].rank_change == 0

    def test_weekly_leaderboard(self):
        daily = {
            "2025-01-01": {"a": 10, "b": 20},
            "2025-01-02": {"a": 15, "b": 5},
        }
        ranked = calculate_weekly_leaderboard(daily)
        assert ranked[0].user_id == "a"
        assert ranked[0].score == 25


class TestStreak:
    def test_new_streak(self):
        s = UserStreak(user_id="u1", activity_type="run")
        result = update_streak(s, datetime(2025, 1, 1))
        assert result.current_streak == 1

    def test_consecutive_days(self):
        s = UserStreak(user_id="u1", activity_type="run")
        s = update_streak(s, datetime(2025, 1, 1))
        s = update_streak(s, datetime(2025, 1, 2))
        s = update_streak(s, datetime(2025, 1, 3))
        assert s.current_streak == 3

    def test_same_day_no_change(self):
        s = UserStreak(user_id="u1", activity_type="run")
        s = update_streak(s, datetime(2025, 1, 1))
        s = update_streak(s, datetime(2025, 1, 1))
        assert s.current_streak == 1

    def test_broken_streak(self):
        s = UserStreak(user_id="u1", activity_type="run")
        s = update_streak(s, datetime(2025, 1, 1))
        s = update_streak(s, datetime(2025, 1, 5))
        assert s.current_streak == 1

    def test_grace_period(self):
        s = UserStreak(user_id="u1", activity_type="run")
        s = update_streak(s, datetime(2025, 1, 1))
        s = update_streak(s, datetime(2025, 1, 3), grace_period_days=2)
        assert s.current_streak == 2

    def test_longest_streak(self):
        s = UserStreak(user_id="u1", activity_type="run")
        s = update_streak(s, datetime(2025, 1, 1))
        s = update_streak(s, datetime(2025, 1, 2))
        s = update_streak(s, datetime(2025, 1, 3))
        s = update_streak(s, datetime(2025, 1, 10))
        assert s.current_streak == 1
        assert s.longest_streak == 3


class TestStreakMultiplier:
    def test_no_streak(self):
        s = UserStreak(user_id="u1", activity_type="run")
        assert calculate_streak_multiplier(s) == 1.0

    def test_week_streak(self):
        s = UserStreak(user_id="u1", activity_type="run", current_streak=7)
        assert calculate_streak_multiplier(s) == 1.6

    def test_max_multiplier(self):
        s = UserStreak(user_id="u1", activity_type="run", current_streak=20)
        assert calculate_streak_multiplier(s) == 2.0


class TestTotalPoints:
    def test_basic(self):
        txns = [
            PointTransaction(user_id="u1", points=100, source="ach", description="Test"),
            PointTransaction(user_id="u1", points=50, source="streak", description="Streak"),
        ]
        assert calculate_total_points(txns) == 150

    def test_empty(self):
        assert calculate_total_points([]) == 0


class TestUserLevel:
    def test_level_zero(self):
        assert calculate_user_level(0) == (0, 0.0)

    def test_level_one(self):
        level, progress = calculate_user_level(100)
        assert level >= 0

    def test_high_points(self):
        level, progress = calculate_user_level(10000)
        assert level > 0


class TestAchievementSummary:
    def test_summary(self):
        achievements = [make_achievement(f"a{i}") for i in range(5)]
        progress = [make_progress(f"a{i}") for i in range(5)]
        progress[0].completed = True
        progress[1].completed = True
        summary = generate_achievement_summary(progress, achievements)
        assert summary["total_achievements"] == 5
        assert summary["completed"] == 2
        assert summary["completion_rate"] == 0.4

    def test_empty(self):
        assert generate_achievement_summary([], [])["total_achievements"] == 0
