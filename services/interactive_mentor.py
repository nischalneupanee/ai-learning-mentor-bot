"""
Interactive AI Mentor for thread-based Q&A.
Provides personalized guidance and status updates.
"""

import logging
from typing import Optional
from config import config
from services.gemini import gemini_service
from services.career_pathway import get_progress_summary, get_milestone_for_points
from utils import safe_json_loads

logger = logging.getLogger(__name__)


MENTOR_QA_PROMPT = """You are an AI Learning Mentor helping students on their AI/ML engineering and research journey.

STUDENT PROFILE:
{user_profile}

CURRENT STATUS:
- Skill Level: {skill_level_name}
- Total Points: {points}
- Current Streak: {streak} days
- Days Active: {days_active}
- Total Logs: {total_logs}

CAREER PATHWAY:
{pathway_info}

RECENT ACTIVITY:
{recent_activity}

STUDENT QUESTION:
"{question}"

Provide a helpful, encouraging response that:
1. Directly answers their question
2. References their current progress and status
3. Gives actionable next steps
4. Relates to their career goal (ML Engineer/AI Researcher)
5. Is concise (3-5 sentences max)

Response (plain text, conversational tone):"""


STATUS_SUMMARY_PROMPT = """You are an AI Learning Mentor creating a comprehensive status report.

STUDENT PROFILE:
{user_profile}

CURRENT MILESTONE: {milestone_name}
Progress: {progress_pct:.1f}% to next milestone

CAREER PATHWAY PROGRESS:
{pathway_info}

RECENT PERFORMANCE (last 7 days):
{recent_stats}

Create a status summary as JSON:
{{
  "overall_status": "brief 2-sentence summary",
  "strengths": ["list of 2-3 strengths"],
  "areas_to_improve": ["list of 2-3 areas"],
  "next_immediate_steps": ["3 specific actionable steps"],
  "motivation_message": "1 encouraging sentence",
  "estimated_time_to_next_level": "realistic estimate with reasoning"
}}

Return ONLY the JSON."""


class InteractiveMentor:
    """Interactive AI mentor for personalized Q&A."""
    
    def __init__(self, state_manager):
        self.state = state_manager
    
    async def answer_question(
        self,
        user_id: int,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Answer a student's question with personalized context.
        
        Args:
            user_id: Discord user ID
            question: Student's question
            context: Additional context (optional)
        
        Returns:
            AI-generated response
        """
        try:
            user_data = self.state.get_user(user_id)
            if not user_data:
                return "I don't have your learning data yet. Start logging your learning journey!"
            
            # Build user profile summary
            user_profile = self._build_user_profile(user_data)
            pathway_info = self._build_pathway_info(user_data)
            recent_activity = self._build_recent_activity(user_data)
            
            skill_level = user_data.get("skill_level", 0)
            level_info = config.SKILL_LEVELS.get(skill_level, {})
            
            # Format prompt
            prompt = MENTOR_QA_PROMPT.format(
                user_profile=user_profile,
                skill_level_name=level_info.get("name", "Beginner"),
                points=user_data.get("points", 0),
                streak=user_data.get("streak", 0),
                days_active=user_data.get("days_active", 0),
                total_logs=user_data.get("total_logs", 0),
                pathway_info=pathway_info,
                recent_activity=recent_activity,
                question=question
            )
            
            # Get AI response
            response = await gemini_service.generate_text(prompt, temperature=0.7)
            
            if not response:
                return "I'm having trouble connecting to my AI brain right now. Try again in a moment!"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return "Something went wrong while generating your response. Please try again!"
    
    async def get_status_report(self, user_id: int) -> dict:
        """
        Generate a comprehensive status report for a user.
        
        Args:
            user_id: Discord user ID
        
        Returns:
            Dictionary with status information
        """
        try:
            user_data = self.state.get_user(user_id)
            if not user_data:
                return {"error": "User data not found"}
            
            # Get progress summary
            progress = get_progress_summary(user_data)
            current_milestone = progress["current_milestone"]
            
            # Build context
            user_profile = self._build_user_profile(user_data)
            pathway_info = self._build_pathway_info(user_data)
            recent_stats = self._build_recent_stats(user_data)
            
            # Format prompt
            prompt = STATUS_SUMMARY_PROMPT.format(
                user_profile=user_profile,
                milestone_name=current_milestone["name"],
                progress_pct=progress["progress_percentage"],
                pathway_info=pathway_info,
                recent_stats=recent_stats
            )
            
            # Get AI response
            response = await gemini_service.generate_text(prompt, temperature=0.6)
            
            if not response:
                return {"error": "Failed to generate status report"}
            
            # Parse JSON response
            status_data = safe_json_loads(response)
            if not status_data:
                return {"error": "Failed to parse AI response"}
            
            # Add progress info
            status_data["progress"] = progress
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error in get_status_report: {e}")
            return {"error": str(e)}
    
    def _build_user_profile(self, user_data: dict) -> str:
        """Build a concise user profile string."""
        points = user_data.get("points", 0)
        streak = user_data.get("streak", 0)
        badges = user_data.get("badges", [])
        topic_coverage = user_data.get("topic_coverage", {})
        
        profile_parts = [
            f"Points: {points}",
            f"Streak: {streak} days",
            f"Topics covered: {', '.join(f'{k}({v})' for k, v in topic_coverage.items() if v > 0) or 'None yet'}",
        ]
        
        if badges:
            profile_parts.append(f"Badges: {len(badges)}")
        
        return " | ".join(profile_parts)
    
    def _build_pathway_info(self, user_data: dict) -> str:
        """Build pathway progress information."""
        progress = get_progress_summary(user_data)
        current = progress["current_milestone"]
        next_m = progress["next_milestone"]
        
        info_parts = [
            f"Current Stage: {current['name']}",
            f"Progress: {progress['progress_percentage']:.1f}%",
        ]
        
        if next_m:
            info_parts.append(f"Next Milestone: {next_m['name']}")
        
        # Add focus areas
        if current.get("focus_areas"):
            info_parts.append(f"Current Focus: {current['focus_areas'][0]}")
        
        return "\n".join(info_parts)
    
    def _build_recent_activity(self, user_data: dict) -> str:
        """Build recent activity summary."""
        last_eval = user_data.get("last_evaluation")
        if not last_eval:
            return "No recent evaluations"
        
        depth = last_eval.get("depth_score", 0)
        concepts = last_eval.get("concepts_detected", [])
        
        return f"Last eval depth: {depth}/10, Concepts: {len(concepts)}"
    
    def _build_recent_stats(self, user_data: dict) -> str:
        """Build recent statistics summary."""
        stats = []
        
        weekly_scores = user_data.get("weekly_scores", [])
        if weekly_scores:
            recent = weekly_scores[-7:]
            avg_depth = sum(s.get("avg_depth", 0) for s in recent) / len(recent) if recent else 0
            stats.append(f"Average depth: {avg_depth:.1f}/10")
        
        total_logs = user_data.get("total_logs", 0)
        days_active = user_data.get("days_active", 0)
        consistency = (total_logs / days_active * 100) if days_active > 0 else 0
        stats.append(f"Consistency: {consistency:.0f}%")
        
        return "\n".join(stats) if stats else "Limited data available"


def init_interactive_mentor(state_manager):
    """Initialize the interactive mentor."""
    return InteractiveMentor(state_manager)
