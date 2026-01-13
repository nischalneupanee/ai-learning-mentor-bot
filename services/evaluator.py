"""
Evaluator service for processing learning logs and generating insights.
Combines local text analysis with Gemini AI for comprehensive evaluation.
"""

import discord
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from config import config
from services.discord_state import DiscordStateManager
from services.gemini import gemini_service, GeminiError
from utils import (
    analyze_message,
    summarize_logs,
    update_concept_frequency,
    calculate_concept_repetition_penalty,
    format_concepts_display,
    today,
    get_effective_date,
    get_last_n_days,
    format_datetime,
    now,
    is_same_day,
    clean_message_content,
)

logger = logging.getLogger(__name__)


class EvaluationResult:
    """Container for evaluation results."""
    
    def __init__(
        self,
        user_id: int,
        date: str,
        analysis: dict,
        mentor_feedback: dict,
        points_earned: int,
        new_concepts: list[str],
        repeated_concepts: list[str],
        repetition_penalty: float,
        local_analysis: dict
    ):
        self.user_id = user_id
        self.date = date
        self.analysis = analysis
        self.mentor_feedback = mentor_feedback
        self.points_earned = points_earned
        self.new_concepts = new_concepts
        self.repeated_concepts = repeated_concepts
        self.repetition_penalty = repetition_penalty
        self.local_analysis = local_analysis
        self.timestamp = format_datetime(now())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "date": self.date,
            "analysis": self.analysis,
            "mentor_feedback": self.mentor_feedback,
            "points_earned": self.points_earned,
            "new_concepts": self.new_concepts,
            "repeated_concepts": self.repeated_concepts,
            "repetition_penalty": self.repetition_penalty,
            "timestamp": self.timestamp,
        }
    
    def get_combined_depth_score(self) -> float:
        """Get combined depth score from AI and local analysis."""
        ai_score = self.analysis.get("depth_score", 5)
        ai_confidence = self.analysis.get("confidence", 0.5)
        local_score = self.local_analysis.get("depth_score", 3) * 2  # Scale 0-5 to 0-10
        
        # Weight by confidence
        if ai_confidence >= 0.7:
            return ai_score
        else:
            # Blend AI and local scores based on confidence
            return (ai_score * ai_confidence) + (local_score * (1 - ai_confidence))


class Evaluator:
    """
    Handles evaluation of learning logs and generates insights.
    """
    
    def __init__(self, bot: discord.Bot, state_manager: DiscordStateManager):
        self.bot = bot
        self.state = state_manager
        self._evaluation_lock = asyncio.Lock()
    
    async def collect_daily_logs(
        self,
        user_id: int,
        date: Optional[str] = None
    ) -> list[tuple[str, datetime]]:
        """
        Collect all valid learning logs for a user on a given date.
        
        Returns:
            List of (content, timestamp) tuples
        """
        target_date = date or get_effective_date()
        logs = []
        
        # Check learning channel
        learning_channel = self.bot.get_channel(config.LEARNING_CHANNEL_ID)
        if learning_channel:
            logs.extend(await self._collect_from_channel(
                learning_channel, user_id, target_date
            ))
        
        # Check user's daily thread
        thread_id = self.state.get_daily_thread(user_id)
        if thread_id:
            try:
                thread = self.bot.get_channel(thread_id)
                if not thread:
                    thread = await self.bot.fetch_channel(thread_id)
                
                if thread:
                    logs.extend(await self._collect_from_channel(
                        thread, user_id, target_date
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch thread {thread_id}: {e}")
        
        # Sort by timestamp
        logs.sort(key=lambda x: x[1])
        
        return logs
    
    async def _collect_from_channel(
        self,
        channel: discord.TextChannel,
        user_id: int,
        target_date: str
    ) -> list[tuple[str, datetime]]:
        """Collect logs from a specific channel."""
        logs = []
        
        try:
            # Calculate time range for the target date
            from utils.time import parse_date, get_timezone
            
            start_dt = parse_date(target_date)
            if not start_dt:
                return logs
            
            end_dt = start_dt + timedelta(days=1)
            
            async for message in channel.history(
                after=start_dt,
                before=end_dt,
                limit=100
            ):
                if message.author.id != user_id:
                    continue
                
                if message.author.bot:
                    continue
                
                content = clean_message_content(message.content)
                
                # Basic qualification check
                if len(content) >= config.MIN_MESSAGE_LENGTH:
                    logs.append((content, message.created_at))
        
        except Exception as e:
            logger.error(f"Error collecting logs from channel: {e}")
        
        return logs
    
    async def evaluate_user(
        self,
        user_id: int,
        force: bool = False
    ) -> Optional[EvaluationResult]:
        """
        Run full evaluation for a user.
        
        Args:
            user_id: User to evaluate
            force: Skip rate limit check
        
        Returns:
            EvaluationResult or None
        """
        async with self._evaluation_lock:
            # Check if already evaluated today
            if not force and self.state.has_evaluated_today(user_id):
                logger.info(f"User {user_id} already evaluated today")
                return None
            
            user = self.state.get_user(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None
            
            # Collect today's logs
            logs = await self.collect_daily_logs(user_id)
            
            if not logs:
                logger.info(f"No logs found for user {user_id}")
                return None
            
            # Prepare logs for analysis
            log_texts = [log[0] for log in logs]
            combined_logs = summarize_logs(log_texts, max_length=2000)
            
            # Local analysis (always available)
            local_results = []
            existing_contents = []
            
            for log_text in log_texts:
                analysis = analyze_message(log_text, existing_contents)
                if analysis["qualifies"]:
                    local_results.append(analysis)
                    existing_contents.append(log_text)
            
            # Aggregate local analysis
            all_concepts = []
            total_depth = 0
            primary_topics = []
            
            for result in local_results:
                all_concepts.extend(result.get("concepts", []))
                total_depth += result.get("depth_score", 0)
                primary_topics.append(result.get("primary_topic", "Mixed"))
            
            avg_local_depth = total_depth / max(len(local_results), 1)
            
            # Get concept frequency
            concept_freq = user.get("concept_frequency", {})
            
            # Calculate repetition penalty
            penalty, repeated = calculate_concept_repetition_penalty(
                all_concepts, concept_freq
            )
            
            # Find new concepts
            new_concepts = [c for c in all_concepts if c not in concept_freq]
            
            local_analysis = {
                "depth_score": avg_local_depth,
                "concepts": all_concepts,
                "primary_topics": list(set(primary_topics)),
                "qualified_logs": len(local_results),
                "total_logs": len(logs),
            }
            
            # AI Analysis (with rate limiting)
            ai_analysis = await gemini_service.analyze_logs(
                user_id,
                combined_logs,
                concept_freq
            )
            
            if not ai_analysis:
                ai_analysis = gemini_service._get_fallback_analysis()
            
            # Get recent evaluations for context
            recent_evals = list(self.state.get_cached_evaluations(user_id, 7).values())
            
            # Generate mentor feedback
            mentor_feedback = await gemini_service.generate_mentor_feedback(
                user_id,
                ai_analysis,
                user,
                recent_evals
            )
            
            if not mentor_feedback:
                mentor_feedback = gemini_service._get_fallback_mentor_feedback(user)
            
            # Calculate points
            base_points = config.BASE_POINTS * len(local_results)
            depth_bonus = 0
            
            combined_depth = (
                ai_analysis.get("depth_score", 5) * ai_analysis.get("confidence", 0.5) +
                avg_local_depth * 2 * (1 - ai_analysis.get("confidence", 0.5))
            )
            
            if combined_depth >= 7:
                depth_bonus = config.DEPTH_BONUS * len(local_results)
            
            # Apply repetition penalty
            total_points = int((base_points + depth_bonus) * penalty)
            
            # Create result
            result = EvaluationResult(
                user_id=user_id,
                date=get_effective_date(),
                analysis=ai_analysis,
                mentor_feedback=mentor_feedback,
                points_earned=total_points,
                new_concepts=new_concepts[:10],
                repeated_concepts=repeated[:10],
                repetition_penalty=penalty,
                local_analysis=local_analysis
            )
            
            # Update state
            await self._apply_evaluation_results(user_id, result, all_concepts)
            
            # Mark as evaluated
            await self.state.mark_evaluated(user_id)
            
            # Cache evaluation
            await self.state.cache_evaluation(
                user_id,
                result.date,
                result.to_dict()
            )
            
            logger.info(f"Completed evaluation for user {user_id}: {total_points} points")
            
            return result
    
    async def _apply_evaluation_results(
        self,
        user_id: int,
        result: EvaluationResult,
        concepts: list[str]
    ) -> None:
        """Apply evaluation results to user state."""
        # Add points
        await self.state.add_points(user_id, result.points_earned)
        
        # Update concept frequency
        await self.state.update_concept_frequency(user_id, concepts)
        
        # Update topic coverage
        user = self.state.get_user(user_id)
        if user:
            coverage = user.get("topic_coverage", {"AI": 0, "ML": 0, "DL": 0, "DS": 0})
            primary = result.analysis.get("primary_focus", "Mixed")
            
            if primary in coverage:
                coverage[primary] += 1
            elif primary == "Mixed":
                for topic in coverage:
                    coverage[topic] += 0.25
            
            await self.state.update_user(user_id, {"topic_coverage": coverage})
        
        # Check for badges
        await self._check_and_award_badges(user_id, result)
        
        # Update skill level
        await self.state.update_skill_level(user_id)
    
    async def _check_and_award_badges(
        self,
        user_id: int,
        result: EvaluationResult
    ) -> list[str]:
        """Check and award any earned badges."""
        awarded = []
        user = self.state.get_user(user_id)
        
        if not user:
            return awarded
        
        existing_badges = user.get("badges", [])
        
        # First log badge
        if "first_log" not in existing_badges and user.get("total_logs", 0) >= 1:
            await self.state.award_badge(user_id, "first_log")
            awarded.append("first_log")
        
        # Streak badges
        streak = user.get("streak", 0)
        
        if "streak_7" not in existing_badges and streak >= 7:
            await self.state.award_badge(user_id, "streak_7")
            awarded.append("streak_7")
        
        if "streak_30" not in existing_badges and streak >= 30:
            await self.state.award_badge(user_id, "streak_30")
            awarded.append("streak_30")
        
        if "streak_100" not in existing_badges and streak >= 100:
            await self.state.award_badge(user_id, "streak_100")
            awarded.append("streak_100")
        
        # Depth master badge
        if "depth_master" not in existing_badges:
            depth = result.get_combined_depth_score()
            if depth >= 9:
                await self.state.award_badge(user_id, "depth_master")
                awarded.append("depth_master")
        
        # All topics badge
        if "all_topics" not in existing_badges:
            coverage = user.get("topic_coverage", {})
            if all(v >= 1 for v in coverage.values()):
                await self.state.award_badge(user_id, "all_topics")
                awarded.append("all_topics")
        
        return awarded
    
    async def simulate_day(
        self,
        user_id: int,
        logs: list[str]
    ) -> dict:
        """
        Simulate evaluation with custom logs (for testing).
        Does not modify state.
        """
        user = self.state.get_user(user_id)
        if not user:
            return {"error": "User not found"}
        
        combined = summarize_logs(logs, max_length=2000)
        concept_freq = user.get("concept_frequency", {})
        
        # Local analysis
        all_concepts = []
        for log in logs:
            analysis = analyze_message(log)
            if analysis["qualifies"]:
                all_concepts.extend(analysis.get("concepts", []))
        
        # AI analysis
        ai_analysis = await gemini_service.analyze_logs(
            user_id,
            combined,
            concept_freq
        )
        
        penalty, repeated = calculate_concept_repetition_penalty(
            all_concepts, concept_freq
        )
        
        base_points = config.BASE_POINTS * len(logs)
        depth_bonus = config.DEPTH_BONUS if ai_analysis.get("depth_score", 5) >= 7 else 0
        total = int((base_points + depth_bonus * len(logs)) * penalty)
        
        return {
            "ai_analysis": ai_analysis,
            "concepts_detected": all_concepts,
            "new_concepts": [c for c in all_concepts if c not in concept_freq],
            "repeated_concepts": repeated,
            "repetition_penalty": penalty,
            "estimated_points": total,
            "qualified_logs": len([l for l in logs if len(l) >= config.MIN_MESSAGE_LENGTH])
        }
    
    async def get_weekly_summary(self, user_id: int) -> Optional[dict]:
        """Generate weekly summary for user."""
        user = self.state.get_user(user_id)
        if not user:
            return None
        
        # Get week's evaluations
        evaluations = self.state.get_cached_evaluations(user_id, 7)
        eval_list = list(evaluations.values())
        
        if not eval_list:
            return {
                "message": "No evaluations this week yet. Keep logging!",
                "_empty": True
            }
        
        # Generate AI summary
        summary = await gemini_service.generate_weekly_summary(
            user_id,
            eval_list,
            user
        )
        
        return summary
    
    def create_evaluation_embed(
        self,
        result: EvaluationResult,
        user: discord.User
    ) -> discord.Embed:
        """Create a Discord embed for evaluation results."""
        analysis = result.analysis
        feedback = result.mentor_feedback
        
        # Determine embed color based on depth score
        depth = result.get_combined_depth_score()
        if depth >= 8:
            color = discord.Color.gold()
        elif depth >= 6:
            color = discord.Color.green()
        elif depth >= 4:
            color = discord.Color.blue()
        else:
            color = discord.Color.orange()
        
        embed = discord.Embed(
            title=f"📊 Daily Evaluation - {user.display_name}",
            description=feedback.get("mentor_feedback", "Keep up the great work!"),
            color=color,
            timestamp=now()
        )
        
        # Primary focus and depth
        focus_emoji = {
            "AI": "🤖", "ML": "📈", "DL": "🧠", "DS": "📊", "Mixed": "🎯"
        }.get(analysis.get("primary_focus", "Mixed"), "📚")
        
        embed.add_field(
            name="Focus Area",
            value=f"{focus_emoji} {analysis.get('primary_focus', 'Mixed')}",
            inline=True
        )
        
        embed.add_field(
            name="Depth Score",
            value=f"{'⭐' * int(depth // 2)} ({depth:.1f}/10)",
            inline=True
        )
        
        embed.add_field(
            name="Points Earned",
            value=f"+{result.points_earned} 💰",
            inline=True
        )
        
        # Concepts
        if result.new_concepts:
            embed.add_field(
                name="🆕 New Concepts",
                value=format_concepts_display(result.new_concepts, 5),
                inline=False
            )
        
        if result.repeated_concepts:
            embed.add_field(
                name="🔄 Reviewed Concepts",
                value=format_concepts_display(result.repeated_concepts, 3),
                inline=False
            )
        
        # Streak health
        health = feedback.get("streak_health", "safe")
        health_emoji = {"safe": "🟢", "at-risk": "🟡", "broken": "🔴"}.get(health, "⚪")
        
        embed.add_field(
            name="Streak Health",
            value=f"{health_emoji} {health.title()}",
            inline=True
        )
        
        embed.add_field(
            name="Mastery Progress",
            value=f"{feedback.get('mastery_progress_percent', 0)}%",
            inline=True
        )
        
        # Next day suggestion
        if feedback.get("next_day_focus"):
            embed.add_field(
                name="📌 Tomorrow's Focus",
                value=feedback["next_day_focus"],
                inline=False
            )
        
        # Confidence indicator
        ai_confidence = analysis.get("confidence", 0)
        if ai_confidence > 0:
            confidence_bar = "█" * int(ai_confidence * 10) + "░" * (10 - int(ai_confidence * 10))
            embed.set_footer(text=f"AI Confidence: [{confidence_bar}] {ai_confidence:.0%}")
        else:
            embed.set_footer(text="⚠️ Fallback analysis used")
        
        return embed


# Global evaluator instance (initialized in bot.py)
evaluator: Optional[Evaluator] = None


def init_evaluator(bot: discord.Bot, state_manager: DiscordStateManager) -> Evaluator:
    """Initialize the global evaluator instance."""
    global evaluator
    evaluator = Evaluator(bot, state_manager)
    return evaluator
