"""
Google Gemini AI integration service.
Handles all AI-powered analysis and mentorship features.
"""

import asyncio
import logging
from typing import Optional
import aiohttp
from datetime import datetime

from config import config, ANALYZER_PROMPT, MENTOR_PROMPT, WEEKLY_SUMMARY_PROMPT
from utils import (
    safe_json_loads,
    safe_json_dumps,
    extract_json_from_text,
    format_datetime,
    now,
)

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Custom exception for Gemini API errors."""
    pass


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    Implements rate limiting and error handling.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_tracker: dict[str, list[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user is within rate limits.
        Returns True if request is allowed.
        """
        from utils import today
        
        user_key = str(user_id)
        date_key = today()
        
        if user_key not in self._rate_limit_tracker:
            self._rate_limit_tracker[user_key] = []
        
        # Filter to today's requests only
        self._rate_limit_tracker[user_key] = [
            dt for dt in self._rate_limit_tracker[user_key]
            if dt.strftime("%Y-%m-%d") == date_key
        ]
        
        return len(self._rate_limit_tracker[user_key]) < config.GEMINI_DAILY_LIMIT_PER_USER
    
    def _record_request(self, user_id: int) -> None:
        """Record an API request for rate limiting."""
        user_key = str(user_id)
        
        if user_key not in self._rate_limit_tracker:
            self._rate_limit_tracker[user_key] = []
        
        self._rate_limit_tracker[user_key].append(now())
    
    async def _call_gemini(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Optional[str]:
        """
        Make a call to Gemini API.
        
        Returns:
            Response text or None on failure
        """
        async with self._lock:
            try:
                session = await self._get_session()
                
                url = self.GEMINI_API_URL.format(model=self.model)
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                        "topP": 0.95,
                        "topK": 40,
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_NONE"
                        }
                    ]
                }
                
                headers = {
                    "Content-Type": "application/json",
                }
                
                params = {
                    "key": self.api_key
                }
                
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 429:
                        logger.warning("Gemini rate limit exceeded")
                        raise GeminiError("Rate limit exceeded")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error {response.status}: {error_text}")
                        raise GeminiError(f"API error: {response.status}")
                    
                    data = await response.json()
                    
                    # Extract response text
                    candidates = data.get("candidates", [])
                    if not candidates:
                        logger.warning("No candidates in Gemini response")
                        return None
                    
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    
                    if not parts:
                        logger.warning("No parts in Gemini response")
                        return None
                    
                    return parts[0].get("text", "")
                    
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling Gemini: {e}")
                raise GeminiError(f"Network error: {e}")
            except asyncio.TimeoutError:
                logger.error("Gemini API timeout")
                raise GeminiError("Request timeout")
            except Exception as e:
                logger.error(f"Unexpected error calling Gemini: {e}")
                raise GeminiError(f"Unexpected error: {e}")
    
    async def analyze_logs(
        self,
        user_id: int,
        logs: str,
        concept_history: dict[str, int]
    ) -> Optional[dict]:
        """
        Analyze learning logs using the Analyzer prompt.
        
        Args:
            user_id: User ID for rate limiting
            logs: Concatenated learning logs
            concept_history: User's concept frequency map
        
        Returns:
            Analysis result dict or None
        """
        if not self._check_rate_limit(user_id):
            logger.warning(f"Rate limit reached for user {user_id}")
            return None
        
        # Format concept history
        if concept_history:
            history_str = ", ".join(
                f"{concept} ({count}x)" 
                for concept, count in sorted(
                    concept_history.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]  # Top 20 concepts
            )
        else:
            history_str = "No previous concept history"
        
        prompt = ANALYZER_PROMPT.format(
            logs=logs,
            concept_history=history_str
        )
        
        try:
            response = await self._call_gemini(prompt, temperature=0.3)
            
            if not response:
                return self._get_fallback_analysis()
            
            # Extract JSON from response
            json_str = extract_json_from_text(response)
            if not json_str:
                logger.warning("Could not extract JSON from Gemini response")
                return self._get_fallback_analysis()
            
            result = safe_json_loads(json_str)
            if not result:
                return self._get_fallback_analysis()
            
            # Validate required fields
            required = [
                "primary_focus", "concepts_detected", "depth_score", "confidence"
            ]
            for field in required:
                if field not in result:
                    logger.warning(f"Missing required field: {field}")
                    return self._get_fallback_analysis()
            
            self._record_request(user_id)
            return result
            
        except GeminiError as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._get_fallback_analysis()
    
    async def generate_mentor_feedback(
        self,
        user_id: int,
        analysis: dict,
        user_stats: dict,
        recent_evaluations: list[dict]
    ) -> Optional[dict]:
        """
        Generate mentor feedback based on analysis.
        
        Args:
            user_id: User ID
            analysis: Today's analysis result
            user_stats: User statistics
            recent_evaluations: List of recent evaluation results
        
        Returns:
            Mentor feedback dict or None
        """
        # Format recent performance
        if recent_evaluations:
            perf_str = "\n".join(
                f"- Day {i+1}: Depth {e.get('depth_score', 'N/A')}, "
                f"Focus: {e.get('primary_focus', 'N/A')}"
                for i, e in enumerate(recent_evaluations[-7:])
            )
        else:
            perf_str = "No recent performance data"
        
        prompt = MENTOR_PROMPT.format(
            analysis=safe_json_dumps(analysis, compact=False),
            streak=user_stats.get("streak", 0),
            points=user_stats.get("points", 0),
            level=config.SKILL_LEVELS.get(
                user_stats.get("skill_level", 0), {}
            ).get("name", "Beginner"),
            days_active=user_stats.get("days_active", 0),
            recent_performance=perf_str
        )
        
        try:
            response = await self._call_gemini(prompt, temperature=0.7)
            
            if not response:
                return self._get_fallback_mentor_feedback(user_stats)
            
            json_str = extract_json_from_text(response)
            if not json_str:
                return self._get_fallback_mentor_feedback(user_stats)
            
            result = safe_json_loads(json_str)
            if not result:
                return self._get_fallback_mentor_feedback(user_stats)
            
            return result
            
        except GeminiError as e:
            logger.error(f"Gemini mentor feedback failed: {e}")
            return self._get_fallback_mentor_feedback(user_stats)
    
    async def generate_weekly_summary(
        self,
        user_id: int,
        weekly_evaluations: list[dict],
        user_stats: dict
    ) -> Optional[dict]:
        """
        Generate weekly summary.
        
        Args:
            user_id: User ID
            weekly_evaluations: List of evaluations for the week
            user_stats: User statistics
        
        Returns:
            Weekly summary dict or None
        """
        if not self._check_rate_limit(user_id):
            logger.warning(f"Rate limit reached for user {user_id}")
            return self._get_fallback_weekly_summary()
        
        # Compile weekly data
        weekly_data = {
            "days_logged": len(weekly_evaluations),
            "evaluations": weekly_evaluations,
            "avg_depth": sum(
                e.get("depth_score", 0) for e in weekly_evaluations
            ) / max(len(weekly_evaluations), 1),
            "topics_covered": list(set(
                e.get("primary_focus", "Mixed") for e in weekly_evaluations
            )),
            "all_concepts": list(set(
                concept
                for e in weekly_evaluations
                for concept in e.get("concepts_detected", [])
            )),
        }
        
        prompt = WEEKLY_SUMMARY_PROMPT.format(
            weekly_data=safe_json_dumps(weekly_data, compact=False),
            streak=user_stats.get("streak", 0),
            points=user_stats.get("points", 0),
            level=config.SKILL_LEVELS.get(
                user_stats.get("skill_level", 0), {}
            ).get("name", "Beginner")
        )
        
        try:
            response = await self._call_gemini(prompt, temperature=0.7)
            
            if not response:
                return self._get_fallback_weekly_summary()
            
            json_str = extract_json_from_text(response)
            if not json_str:
                return self._get_fallback_weekly_summary()
            
            result = safe_json_loads(json_str)
            if not result:
                return self._get_fallback_weekly_summary()
            
            self._record_request(user_id)
            return result
            
        except GeminiError as e:
            logger.error(f"Gemini weekly summary failed: {e}")
            return self._get_fallback_weekly_summary()
    
    async def generate_goal_trajectory(
        self,
        user_stats: dict,
        recent_evaluations: list[dict]
    ) -> str:
        """
        Generate personalized mastery trajectory/goals.
        
        Returns:
            Goal trajectory text
        """
        prompt = f"""You are an AI Learning Mentor. Based on the student's stats, 
generate a personalized learning trajectory toward mastery in AI/ML/DL/Data Science.

Student Stats:
- Points: {user_stats.get('points', 0)}
- Streak: {user_stats.get('streak', 0)} days
- Level: {config.SKILL_LEVELS.get(user_stats.get('skill_level', 0), {}).get('name', 'Beginner')}
- Days Active: {user_stats.get('days_active', 0)}
- Topics Covered: {user_stats.get('topic_coverage', {})}

Recent Focus Areas: {[e.get('primary_focus') for e in recent_evaluations[-5:]]}

Provide a concise, actionable learning trajectory in 3-4 paragraphs covering:
1. Current position assessment
2. Recommended next steps (specific topics/projects)
3. Timeline to reach next skill level
4. Long-term mastery path

Be encouraging but realistic. Use emojis sparingly for visual appeal."""
        
        try:
            response = await self._call_gemini(prompt, temperature=0.8, max_tokens=512)
            return response or self._get_fallback_trajectory()
        except GeminiError:
            return self._get_fallback_trajectory()
    
    # Fallback responses for when API fails
    
    def _get_fallback_analysis(self) -> dict:
        """Get fallback analysis when Gemini fails."""
        return {
            "primary_focus": "Mixed",
            "concepts_detected": [],
            "new_concepts": [],
            "repeated_concepts": [],
            "depth_score": 5,
            "technical_indicators": [],
            "confidence": 0.0,
            "_fallback": True
        }
    
    def _get_fallback_mentor_feedback(self, user_stats: dict) -> dict:
        """Get fallback mentor feedback."""
        streak = user_stats.get("streak", 0)
        
        if streak >= 7:
            feedback = "Keep up the consistent work! Your dedication is showing."
        elif streak >= 3:
            feedback = "Good progress! Stay consistent to build momentum."
        else:
            feedback = "Every learning session counts. Keep pushing forward!"
        
        return {
            "consistency_score": 5,
            "mastery_progress_percent": min(user_stats.get("points", 0) // 50, 100),
            "mentor_feedback": feedback,
            "next_day_focus": "Continue exploring current topics",
            "streak_health": user_stats.get("streak_health", "safe"),
            "motivational_note": "Small steps lead to big achievements!",
            "areas_for_improvement": ["Consistency", "Depth", "Variety"],
            "confidence": 0.0,
            "_fallback": True
        }
    
    def _get_fallback_weekly_summary(self) -> dict:
        """Get fallback weekly summary."""
        return {
            "week_rating": "C",
            "total_concepts_learned": 0,
            "strongest_area": "Mixed",
            "weakest_area": "Mixed",
            "consistency_trend": "stable",
            "depth_trend": "stable",
            "weekly_feedback": "Keep learning! Weekly AI analysis unavailable.",
            "goals_for_next_week": [
                "Log daily learnings",
                "Explore new concepts",
                "Review previous material"
            ],
            "celebration": "You're committed to learning!",
            "_fallback": True
        }
    
    def _get_fallback_trajectory(self) -> str:
        """Get fallback trajectory text."""
        return """📊 **Your Learning Trajectory**

Based on your current progress, you're on a solid path toward mastery!

**Next Steps:**
1. Focus on building foundational understanding
2. Apply concepts through practical projects
3. Explore connections between AI/ML/DL domains

**Timeline:** Continue your current pace for steady improvement.

*Keep logging your daily learnings to get personalized AI-powered insights!*"""
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Get remaining API requests for user today."""
        from utils import today
        
        user_key = str(user_id)
        date_key = today()
        
        if user_key not in self._rate_limit_tracker:
            return config.GEMINI_DAILY_LIMIT_PER_USER
        
        today_requests = [
            dt for dt in self._rate_limit_tracker[user_key]
            if dt.strftime("%Y-%m-%d") == date_key
        ]
        
        return max(0, config.GEMINI_DAILY_LIMIT_PER_USER - len(today_requests))


# Global service instance
gemini_service = GeminiService()
