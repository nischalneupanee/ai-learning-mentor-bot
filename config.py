"""
Configuration module for AI Learning Mentor Bot.
All settings are loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    """Immutable bot configuration."""
    
    # Discord Settings
    DISCORD_TOKEN: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    GUILD_ID: int = field(default_factory=lambda: int(os.getenv("GUILD_ID", "0")))
    
    # Channel IDs
    STATE_CHANNEL_ID: int = field(default_factory=lambda: int(os.getenv("STATE_CHANNEL_ID", "0")))
    LEARNING_CHANNEL_ID: int = field(default_factory=lambda: int(os.getenv("LEARNING_CHANNEL_ID", "0")))
    DASHBOARD_CHANNEL_ID: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_CHANNEL_ID", "0")))
    DAILY_THREADS_CHANNEL_ID: int = field(default_factory=lambda: int(os.getenv("DAILY_THREADS_CHANNEL_ID", "0")))
    
    # Gemini API
    GEMINI_API_KEY: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    
    # User IDs (two users)
    USER_IDS: tuple = field(default_factory=lambda: tuple(
        int(uid.strip()) for uid in os.getenv("USER_IDS", "").split(",") if uid.strip()
    ))
    
    # Timezone
    TIMEZONE: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Kathmandu"))
    
    # Bot Settings
    BOT_PREFIX: str = "/"
    STATE_VERSION: int = 2
    
    # Tracking Settings
    MIN_MESSAGE_LENGTH: int = 30
    BASE_POINTS: int = 10
    DEPTH_BONUS: int = 5
    STREAK_GRACE_HOUR: int = 3  # 3 AM grace period
    
    # Rate Limits
    GEMINI_DAILY_LIMIT_PER_USER: int = 1
    DASHBOARD_REFRESH_SECONDS: int = 300
    
    # Skill Levels
    SKILL_LEVELS: dict = field(default_factory=lambda: {
        0: {"name": "Beginner", "min_points": 0, "emoji": "🌱"},
        1: {"name": "Intermediate", "min_points": 500, "emoji": "📚"},
        2: {"name": "Advanced", "min_points": 2000, "emoji": "🚀"},
        3: {"name": "Researcher", "min_points": 5000, "emoji": "🎓"},
    })
    
    # Badges
    BADGES: dict = field(default_factory=lambda: {
        "first_log": {"name": "First Steps", "emoji": "👶", "description": "Logged first learning entry"},
        "streak_7": {"name": "Week Warrior", "emoji": "🔥", "description": "7-day streak"},
        "streak_30": {"name": "Month Master", "emoji": "💎", "description": "30-day streak"},
        "streak_100": {"name": "Century Scholar", "emoji": "👑", "description": "100-day streak"},
        "depth_master": {"name": "Deep Diver", "emoji": "🧠", "description": "Achieved depth score 9+"},
        "all_topics": {"name": "Renaissance Mind", "emoji": "🌟", "description": "Covered all 4 domains"},
        "consistent": {"name": "Consistency King", "emoji": "⚡", "description": "10 consecutive high-quality days"},
    })
    
    # Topics
    TOPICS: tuple = ("AI", "ML", "DL", "DS")
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN is required")
        if not self.GUILD_ID:
            errors.append("GUILD_ID is required")
        if not self.STATE_CHANNEL_ID:
            errors.append("STATE_CHANNEL_ID is required")
        if not self.LEARNING_CHANNEL_ID:
            errors.append("LEARNING_CHANNEL_ID is required")
        if not self.DASHBOARD_CHANNEL_ID:
            errors.append("DASHBOARD_CHANNEL_ID is required")
        if not self.DAILY_THREADS_CHANNEL_ID:
            errors.append("DAILY_THREADS_CHANNEL_ID is required")
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        if len(self.USER_IDS) != 2:
            errors.append("Exactly 2 USER_IDS are required")
            
        return errors


# Global config instance
config = BotConfig()


# Gemini Prompt Templates
ANALYZER_PROMPT = """You are an AI Learning Analyzer. Analyze the following learning logs from a student studying AI/ML/DL/Data Science.

STUDENT'S LEARNING LOGS FOR TODAY:
---
{logs}
---

STUDENT'S CONCEPT HISTORY (concepts they've covered before, with frequency):
{concept_history}

Analyze the logs and return ONLY valid JSON (no markdown, no explanation):
{{
  "primary_focus": "AI" | "ML" | "DL" | "DS" | "Mixed",
  "concepts_detected": ["list", "of", "concepts", "max 10"],
  "new_concepts": ["concepts not in history"],
  "repeated_concepts": ["concepts already in history"],
  "depth_score": 1-10,
  "technical_indicators": ["specific technical terms found"],
  "confidence": 0.0-1.0
}}

SCORING GUIDE:
- depth_score 1-3: Basic/surface level understanding
- depth_score 4-6: Intermediate with some technical depth
- depth_score 7-9: Advanced with strong technical understanding
- depth_score 10: Research-level depth

Penalize repeated concepts (lower depth_score if mostly reviewing old material).
Be strict but fair. Return ONLY the JSON object."""

MENTOR_PROMPT = """You are an AI Learning Mentor providing personalized feedback to a student.

TODAY'S ANALYSIS:
{analysis}

STUDENT STATS:
- Current Streak: {streak} days
- Total Points: {points}
- Skill Level: {level}
- Days Active: {days_active}

RECENT PERFORMANCE (last 7 days):
{recent_performance}

Provide mentorship feedback as ONLY valid JSON (no markdown, no explanation):
{{
  "consistency_score": 1-10,
  "mastery_progress_percent": 0-100,
  "mentor_feedback": "2-3 concise, encouraging but honest sentences",
  "next_day_focus": "specific topic suggestion based on gaps",
  "streak_health": "safe" | "at-risk" | "broken",
  "motivational_note": "one short motivational sentence",
  "areas_for_improvement": ["max 3 specific areas"],
  "confidence": 0.0-1.0
}}

Be encouraging but honest. Focus on growth. Return ONLY the JSON object."""

WEEKLY_SUMMARY_PROMPT = """You are an AI Learning Mentor creating a weekly summary.

WEEKLY DATA:
{weekly_data}

STUDENT PROFILE:
- Streak: {streak} days
- Total Points: {points}
- Level: {level}

Create a comprehensive but concise weekly summary as ONLY valid JSON:
{{
  "week_rating": "A" | "B" | "C" | "D" | "F",
  "total_concepts_learned": 0,
  "strongest_area": "AI" | "ML" | "DL" | "DS",
  "weakest_area": "AI" | "ML" | "DL" | "DS",
  "consistency_trend": "improving" | "stable" | "declining",
  "depth_trend": "improving" | "stable" | "declining",
  "weekly_feedback": "3-4 sentence comprehensive feedback",
  "goals_for_next_week": ["3 specific actionable goals"],
  "celebration": "something positive to celebrate, even if small"
}}

Return ONLY the JSON object."""


# Default State Template
DEFAULT_STATE = {
    "state_version": config.STATE_VERSION,
    "last_updated": None,
    "bot_metadata": {
        "version": "1.0.0",
        "started_at": None,
        "total_evaluations": 0,
    },
    "users": {},
    "daily_flags": {},
    "evaluation_cache": {},
}


def get_default_user_state(user_id: int, username: str) -> dict:
    """Get default user state structure."""
    return {
        "user_id": user_id,
        "username": username,
        "points": 0,
        "streak": 0,
        "max_streak": 0,
        "last_log_date": None,
        "streak_health": "safe",
        "skill_level": 0,
        "days_active": 0,
        "total_logs": 0,
        "badges": [],
        "concept_frequency": {},
        "topic_coverage": {"AI": 0, "ML": 0, "DL": 0, "DS": 0},
        "weekly_scores": [],
        "last_evaluation": None,
        "evaluation_count": 0,
        "created_at": None,
        "daily_thread_id": None,
    }
