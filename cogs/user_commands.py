"""
User Commands Cog - Enhanced user-facing commands for learning management.
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from config import config
from services.discord_state import DiscordStateManager
from services.evaluator import Evaluator
from services.interactive_mentor import init_interactive_mentor
from services.career_pathway import get_progress_summary, get_recommendations_for_level
from utils import (
    now,
    today,
    format_datetime,
    get_streak_status_emoji,
)

logger = logging.getLogger(__name__)


class UserCommandsCog(commands.Cog):
    """Enhanced user commands for learning management."""
    
    def __init__(
        self,
        bot: discord.Bot,
        state_manager: DiscordStateManager,
        evaluator: Evaluator
    ):
        self.bot = bot
        self.state = state_manager
        self.evaluator = evaluator
        self.mentor = init_interactive_mentor(state_manager)
    
    @discord.slash_command(
        name="help",
        description="Show all available commands and how to use them"
    )
    async def help_command(self, ctx: discord.ApplicationContext) -> None:
        """Display comprehensive help."""
        embed = discord.Embed(
            title="🤖 AI Learning Mentor Bot - Commands",
            description="Your personal AI-powered learning companion for ML/AI mastery!",
            color=discord.Color.blue(),
            timestamp=now()
        )
        
        # User Commands
        embed.add_field(
            name="📚 Learning & Progress",
            value=(
                "`/mystatus` - AI-generated comprehensive status report\n"
                "`/ask <question>` - Ask the AI mentor anything\n"
                "`/stats` - View your learning statistics\n"
                "`/progress` - Career pathway progress\n"
                "`/todayplan` - Get AI daily study plan\n"
                "`/streak` - Check streak status"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Insights & Analytics",
            value=(
                "`/insights` - Deep learning pattern analysis\n"
                "`/concepts` - All learned concepts\n"
                "`/weaknesses` - Areas needing focus\n"
                "`/strengths` - What you excel at\n"
                "`/leaderboard` - Global rankings"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏰ Productivity",
            value=(
                "`/reminder <time> <message>` - Set reminder\n"
                "`/focus <minutes>` - Start focus timer\n"
                "`/goals` - Manage learning goals"
            ),
            inline=False
        )
        
        # Admin Commands (if admin)
        if ctx.author.guild_permissions.administrator:
            embed.add_field(
                name="🛡️ Admin Commands",
                value=(
                    "`/admin setup_channels` - Auto-create channels\n"
                    "`/admin health` - System health check\n"
                    "`/admin backup_state` - Backup data\n"
                    "See `/admin help` for full admin commands"
                ),
                inline=False
            )
        
        embed.add_field(
            name="🎯 Quick Start",
            value=(
                "1️⃣ Post learning logs in <#" + str(config.LEARNING_CHANNEL_ID) + ">\n"
                "2️⃣ Use `/mystatus` to see your progress\n"
                "3️⃣ Ask questions with `/ask`\n"
                "4️⃣ Check daily plan with `/todayplan`"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: Type /ask <question> to get personalized AI help anytime!")
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @discord.slash_command(
        name="stats",
        description="View your detailed learning statistics"
    )
    async def stats_command(self, ctx: discord.ApplicationContext) -> None:
        """Show user statistics."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        await ctx.defer()
        
        try:
            user_data = self.state.get_user(ctx.author.id)
            if not user_data:
                await ctx.respond("❌ No data found. Start logging your learning!", ephemeral=True)
                return
            
            points = user_data.get("total_points", 0)
            streak = user_data.get("current_streak", 0)
            best_streak = user_data.get("best_streak", 0)
            total_logs = user_data.get("total_logs", 0)
            concepts = user_data.get("concepts_learned", [])
            
            # Career progress
            progress = get_progress_summary(points)
            
            embed = discord.Embed(
                title=f"📊 Learning Stats - {ctx.author.display_name}",
                color=discord.Color.green(),
                timestamp=now()
            )
            
            embed.add_field(
                name="🎯 Career Progress",
                value=(
                    f"**{progress['current_milestone']['title']}**\n"
                    f"{progress['progress_bar']}\n"
                    f"{points}/{progress['next_milestone']['min_points']} points to next level"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📈 Statistics",
                value=(
                    f"**Total Points:** {points:,}\n"
                    f"**Total Logs:** {total_logs:,}\n"
                    f"**Concepts Learned:** {len(concepts)}"
                ),
                inline=True
            )
            
            embed.add_field(
                name=f"{get_streak_status_emoji(streak)} Streaks",
                value=(
                    f"**Current:** {streak} days\n"
                    f"**Best:** {best_streak} days\n"
                    f"**Status:** {'🔥 On fire!' if streak >= 7 else '💪 Keep going!'}"
                ),
                inline=True
            )
            
            # Top concepts
            if concepts:
                top_concepts = sorted(
                    [(c, concepts.count(c)) for c in set(concepts)],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                concepts_str = "\n".join(
                    f"• {name} ({count}x)" for name, count in top_concepts
                )
                
                embed.add_field(
                    name="🧠 Top Concepts",
                    value=concepts_str,
                    inline=False
                )
            
            embed.set_footer(text="💡 Use /insights for AI-powered deep analysis")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}", exc_info=True)
            await ctx.respond("❌ Error fetching stats. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="progress",
        description="View your career pathway progress and milestones"
    )
    async def progress_command(self, ctx: discord.ApplicationContext) -> None:
        """Show career pathway progress."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        await ctx.defer()
        
        try:
            user_data = self.state.get_user(ctx.author.id)
            if not user_data:
                await ctx.respond("❌ No data found. Start logging your learning!", ephemeral=True)
                return
            
            points = user_data.get("total_points", 0)
            progress = get_progress_summary(points)
            
            embed = discord.Embed(
                title="🎓 Career Pathway Progress",
                description=f"**Path:** ML Engineer & AI Researcher\n**Your Journey:** {progress['current_milestone']['title']}",
                color=discord.Color.gold(),
                timestamp=now()
            )
            
            # Current milestone details
            current = progress['current_milestone']
            embed.add_field(
                name=f"{current['emoji']} Current Stage",
                value=f"**{current['title']}**\n{current['description']}",
                inline=False
            )
            
            # Progress bar
            embed.add_field(
                name="📊 Progress to Next Level",
                value=f"{progress['progress_bar']}\n{points:,}/{progress['next_milestone']['min_points']:,} points",
                inline=False
            )
            
            # Focus areas
            if current.get('focus_areas'):
                focus_str = "\n".join(f"• {area}" for area in current['focus_areas'])
                embed.add_field(
                    name="🎯 Focus Areas",
                    value=focus_str,
                    inline=True
                )
            
            # Recommended learning
            recommendations = get_recommendations_for_level(current['level'])
            if recommendations:
                rec_str = "\n".join(f"• {rec}" for rec in recommendations[:5])
                embed.add_field(
                    name="📚 Recommended Topics",
                    value=rec_str,
                    inline=True
                )
            
            # All milestones overview
            all_milestones = progress.get('all_milestones', [])
            if all_milestones:
                milestones_str = "\n".join(
                    f"{'✅' if m['level'] <= current['level'] else '⬜'} {m['emoji']} {m['title']} ({m['min_points']:,}+ pts)"
                    for m in all_milestones
                )
                embed.add_field(
                    name="🗺️ Full Pathway",
                    value=milestones_str,
                    inline=False
                )
            
            embed.set_footer(text="💡 Use /todayplan to get personalized daily study plan")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in progress command: {e}", exc_info=True)
            await ctx.respond("❌ Error fetching progress. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="todayplan",
        description="Get AI-generated personalized study plan for today"
    )
    async def todayplan_command(self, ctx: discord.ApplicationContext) -> None:
        """Generate personalized daily study plan."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        await ctx.defer()
        
        try:
            # Get comprehensive status from mentor
            status_report = await self.mentor.get_status_report(ctx.author.id)
            
            # Generate daily plan
            user_data = self.state.get_user(ctx.author.id)
            points = user_data.get("total_points", 0)
            concepts = user_data.get("concepts_learned", [])
            recent_logs = user_data.get("message_history", [])[-10:]
            
            # Get career recommendations
            progress = get_progress_summary(points)
            current_level = progress['current_milestone']['level']
            recommendations = get_recommendations_for_level(current_level)
            
            prompt = f"""Generate a personalized daily study plan for an AI/ML learner.

Current Status:
{status_report}

Career Level: {progress['current_milestone']['title']}
Total Points: {points}
Recent Activity: {len(recent_logs)} logs in last sessions

Create a detailed 4-6 hour study plan for today with:
1. Morning session (2-3 hours) - Deep focus on core concepts
2. Afternoon session (1-2 hours) - Practice and implementation
3. Evening session (1 hour) - Review and concept reinforcement

Include:
- Specific topics from recommended areas: {', '.join(recommendations[:3])}
- Practical exercises
- Resources (videos, articles, docs)
- Break times
- Success metrics for the day

Make it actionable and motivating!"""
            
            plan = await self.mentor.answer_question(ctx.author.id, prompt)
            
            embed = discord.Embed(
                title=f"📅 Today's Study Plan - {ctx.author.display_name}",
                description=plan[:2000],  # Discord limit
                color=discord.Color.blue(),
                timestamp=now()
            )
            
            embed.add_field(
                name="🎯 Today's Focus",
                value=f"Career Stage: {progress['current_milestone']['title']}\nTarget: Make progress toward next milestone!",
                inline=False
            )
            
            embed.set_footer(text="💡 Ask /ask <question> if you need help with any topic!")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in todayplan command: {e}", exc_info=True)
            await ctx.respond("❌ Error generating plan. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="insights",
        description="Get AI-powered deep analysis of your learning patterns"
    )
    async def insights_command(self, ctx: discord.ApplicationContext) -> None:
        """Generate learning insights."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        await ctx.defer()
        
        try:
            user_data = self.state.get_user(ctx.author.id)
            if not user_data or user_data.get("total_logs", 0) < 5:
                await ctx.respond(
                    "❌ Not enough data for insights. Log at least 5 learning sessions first!",
                    ephemeral=True
                )
                return
            
            recent_logs = user_data.get("message_history", [])[-20:]
            concepts = user_data.get("concepts_learned", [])
            points = user_data.get("total_points", 0)
            streak = user_data.get("current_streak", 0)
            
            prompt = f"""Analyze this learner's patterns and provide insights:

Total Points: {points}
Current Streak: {streak} days
Recent Logs: {len(recent_logs)} entries
Concepts Learned: {len(concepts)} unique concepts
Most Common Concepts: {', '.join(list(set(concepts))[:10])}

Provide:
1. **Learning Patterns**: What patterns do you see in their approach?
2. **Strengths**: What are they doing exceptionally well?
3. **Improvements**: Specific areas to focus on
4. **Recommendations**: 3-5 actionable suggestions
5. **Motivation**: Encouraging message based on their progress

Be specific, insightful, and motivating!"""
            
            insights = await self.mentor.answer_question(ctx.author.id, prompt)
            
            embed = discord.Embed(
                title=f"🔍 Learning Insights - {ctx.author.display_name}",
                description=insights[:4000],
                color=discord.Color.purple(),
                timestamp=now()
            )
            
            embed.set_footer(text="💡 Use these insights to optimize your learning strategy!")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in insights command: {e}", exc_info=True)
            await ctx.respond("❌ Error generating insights. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="streak",
        description="Check your current streak status and history"
    )
    async def streak_command(self, ctx: discord.ApplicationContext) -> None:
        """Show streak information."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        try:
            user_data = self.state.get_user(ctx.author.id)
            if not user_data:
                await ctx.respond("❌ No data found. Start your streak today!", ephemeral=True)
                return
            
            current_streak = user_data.get("current_streak", 0)
            best_streak = user_data.get("best_streak", 0)
            last_log = user_data.get("last_log_date")
            
            embed = discord.Embed(
                title=f"{get_streak_status_emoji(current_streak)} Streak Status",
                color=discord.Color.orange() if current_streak >= 7 else discord.Color.blue(),
                timestamp=now()
            )
            
            embed.add_field(
                name="📊 Current Status",
                value=(
                    f"**Current Streak:** {current_streak} days\n"
                    f"**Best Streak:** {best_streak} days\n"
                    f"**Last Log:** {last_log or 'Never'}"
                ),
                inline=False
            )
            
            # Streak milestones
            milestones = [7, 14, 30, 50, 100]
            next_milestone = next((m for m in milestones if m > current_streak), None)
            
            if next_milestone:
                days_to_go = next_milestone - current_streak
                embed.add_field(
                    name="🎯 Next Milestone",
                    value=f"{next_milestone} days ({days_to_go} days to go!)",
                    inline=True
                )
            
            # Motivational message
            if current_streak == 0:
                message = "Start your streak today! Even 10 minutes of learning counts."
            elif current_streak < 7:
                message = f"Great start! Just {7 - current_streak} more days to reach your first milestone!"
            elif current_streak < 30:
                message = f"You're on fire! 🔥 Keep this momentum going!"
            else:
                message = f"Incredible dedication! You're in the top tier of learners! 🏆"
            
            embed.add_field(
                name="💪 Motivation",
                value=message,
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in streak command: {e}", exc_info=True)
            await ctx.respond("❌ Error checking streak. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="concepts",
        description="View all concepts you've learned"
    )
    async def concepts_command(self, ctx: discord.ApplicationContext) -> None:
        """Show learned concepts."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You are not enrolled in the learning program.", ephemeral=True)
            return
        
        try:
            user_data = self.state.get_user(ctx.author.id)
            if not user_data:
                await ctx.respond("❌ No data found.", ephemeral=True)
                return
            
            concepts = user_data.get("concepts_learned", [])
            
            if not concepts:
                await ctx.respond("❌ No concepts learned yet. Start logging your learning!", ephemeral=True)
                return
            
            # Count occurrences
            concept_counts = {}
            for concept in concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
            
            # Sort by frequency
            sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)
            
            embed = discord.Embed(
                title=f"🧠 Concepts Learned - {ctx.author.display_name}",
                description=f"Total: {len(concepts)} mentions across {len(concept_counts)} unique concepts",
                color=discord.Color.teal(),
                timestamp=now()
            )
            
            # Top concepts
            top_20 = sorted_concepts[:20]
            concepts_text = "\n".join(
                f"{'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else '▫️'} **{concept}** ({count}x)"
                for i, (concept, count) in enumerate(top_20)
            )
            
            embed.add_field(
                name="📚 Most Practiced",
                value=concepts_text,
                inline=False
            )
            
            if len(sorted_concepts) > 20:
                embed.set_footer(text=f"Showing top 20 of {len(sorted_concepts)} concepts")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in concepts command: {e}", exc_info=True)
            await ctx.respond("❌ Error fetching concepts. Please try again.", ephemeral=True)
    
    @discord.slash_command(
        name="leaderboard",
        description="View the global learning leaderboard"
    )
    async def leaderboard_command(self, ctx: discord.ApplicationContext) -> None:
        """Show leaderboard."""
        await ctx.defer()
        
        try:
            # Get all users
            users_data = []
            for user_id in config.USER_IDS:
                user_data = self.state.get_user(user_id)
                if user_data:
                    try:
                        member = await ctx.guild.fetch_member(user_id)
                        users_data.append({
                            'id': user_id,
                            'name': member.display_name if member else f"User {user_id}",
                            'points': user_data.get('total_points', 0),
                            'streak': user_data.get('current_streak', 0),
                            'logs': user_data.get('total_logs', 0)
                        })
                    except:
                        pass
            
            if not users_data:
                await ctx.respond("❌ No data available for leaderboard.", ephemeral=True)
                return
            
            # Sort by points
            users_data.sort(key=lambda x: x['points'], reverse=True)
            
            embed = discord.Embed(
                title="🏆 Learning Leaderboard",
                description="Top learners in the AI/ML journey!",
                color=discord.Color.gold(),
                timestamp=now()
            )
            
            medals = ['🥇', '🥈', '🥉']
            
            for i, user in enumerate(users_data[:10]):
                medal = medals[i] if i < 3 else f"**{i+1}.**"
                
                progress = get_progress_summary(user['points'])
                level_emoji = progress['current_milestone']['emoji']
                
                embed.add_field(
                    name=f"{medal} {user['name']}",
                    value=(
                        f"{level_emoji} **{user['points']:,}** points\n"
                        f"🔥 {user['streak']} day streak | 📝 {user['logs']} logs"
                    ),
                    inline=False
                )
            
            embed.set_footer(text="💡 Keep learning to climb the ranks!")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}", exc_info=True)
            await ctx.respond("❌ Error generating leaderboard. Please try again.", ephemeral=True)


def setup(bot: discord.Bot) -> None:
    """Load the cog."""
    # Get managers from bot
    state_manager = getattr(bot, 'state_manager', None)
    evaluator = getattr(bot, 'evaluator', None)
    
    if state_manager and evaluator:
        bot.add_cog(UserCommandsCog(bot, state_manager, evaluator))
        logger.info("UserCommandsCog loaded")
    else:
        logger.error("Failed to load UserCommandsCog - missing dependencies")
