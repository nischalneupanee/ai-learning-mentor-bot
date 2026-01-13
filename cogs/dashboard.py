"""
Dashboard Cog - Handles stats display, leaderboard, and visual progress tracking.
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
from typing import Optional

from config import config
from services.discord_state import DiscordStateManager
from services.evaluator import Evaluator
from services.career_pathway import get_progress_summary, get_milestone_for_points
from utils import (
    now,
    today,
    format_datetime,
    get_streak_status_emoji,
    format_concepts_display,
    get_last_n_days,
)

logger = logging.getLogger(__name__)


class DashboardCog(commands.Cog):
    """Cog for displaying stats, leaderboards, and dashboards."""
    
    def __init__(
        self,
        bot: discord.Bot,
        state_manager: DiscordStateManager,
        evaluator: Evaluator
    ):
        self.bot = bot
        self.state = state_manager
        self.evaluator = evaluator
        self._dashboard_message_id: Optional[int] = None
        
        # Start tasks immediately
        try:
            self.dashboard_refresh_task.start()
            self.daily_evaluation_task.start()
            logger.info("DashboardCog: Tasks started in __init__")
        except Exception as e:
            logger.error(f"DashboardCog: Error starting tasks: {e}", exc_info=True)
    
    def cog_unload(self) -> None:
        """Called when cog is unloaded."""
        try:
            self.dashboard_refresh_task.cancel()
            self.daily_evaluation_task.cancel()
            logger.info("Dashboard cog unloaded, tasks cancelled")
        except Exception as e:
            logger.error(f"Error stopping dashboard tasks: {e}")
    
    @tasks.loop(seconds=config.DASHBOARD_REFRESH_SECONDS)
    async def dashboard_refresh_task(self) -> None:
        """Periodically refresh the dashboard."""
        try:
            await self._update_dashboard()
        except Exception as e:
            logger.error(f"Error in dashboard refresh task: {e}", exc_info=True)
    
    @dashboard_refresh_task.before_loop
    async def before_dashboard_refresh(self) -> None:
        """Wait for bot to be ready."""
        try:
            await self.bot.wait_until_ready()
            # Initial delay to let state load
            await asyncio.sleep(7)
            logger.info("DashboardCog: Starting initial dashboard creation...")
            # Create initial dashboard
            await self._update_dashboard()
            logger.info("DashboardCog: Initial dashboard created successfully!")
        except Exception as e:
            logger.error(f"DashboardCog: Error in dashboard before_loop: {e}", exc_info=True)
    
    @tasks.loop(hours=1)
    async def daily_evaluation_task(self) -> None:
        """Run daily evaluations for all users."""
        try:
            # Check if it's around 11 PM (good time for daily summary)
            current_hour = now().hour
            
            if current_hour == 23:  # 11 PM
                for user_id in config.USER_IDS:
                    try:
                        result = await self.evaluator.evaluate_user(user_id)
                        if result:
                            await self._post_evaluation(user_id, result)
                    except Exception as e:
                        logger.error(f"Error evaluating user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error in daily evaluation task: {e}", exc_info=True)
    
    @daily_evaluation_task.before_loop
    async def before_daily_evaluation(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()
    
    async def _update_dashboard(self) -> None:
        """Update the persistent dashboard embed."""
        try:
            logger.debug("Starting dashboard update...")
            channel = self.bot.get_channel(config.DASHBOARD_CHANNEL_ID)
            if not channel:
                logger.debug(f"Fetching channel {config.DASHBOARD_CHANNEL_ID}...")
                channel = await self.bot.fetch_channel(config.DASHBOARD_CHANNEL_ID)
            
            if not channel:
                logger.error(f"Dashboard channel {config.DASHBOARD_CHANNEL_ID} not found")
                return
            
            logger.debug("Creating dashboard embed...")
            embed = await self._create_dashboard_embed()
            
            # Find or create dashboard message
            if self._dashboard_message_id:
                try:
                    message = await channel.fetch_message(self._dashboard_message_id)
                    await message.edit(embed=embed)
                    logger.debug("Updated existing dashboard message")
                    return
                except discord.NotFound:
                    logger.debug("Dashboard message not found, will create new one")
                    self._dashboard_message_id = None
            
            # Look for existing pinned dashboard
            logger.debug("Checking for existing pinned dashboard...")
            pins = await channel.pins()
            for pin in pins:
                if pin.author.id == self.bot.user.id and pin.embeds:
                    if "Learning Dashboard" in pin.embeds[0].title:
                        self._dashboard_message_id = pin.id
                        await pin.edit(embed=embed)
                        logger.info(f"Updated existing pinned dashboard {pin.id}")
                        return
            
            # Create new dashboard
            logger.info("Creating new dashboard message...")
            message = await channel.send(embed=embed)
            await message.pin()
            self._dashboard_message_id = message.id
            logger.info(f"Created and pinned new dashboard message {message.id}")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}", exc_info=True)
    
    async def _create_dashboard_embed(self) -> discord.Embed:
        """Create the main dashboard embed."""
        embed = discord.Embed(
            title="📊 AI/ML Learning Dashboard",
            description="🎯 **Goal:** AI/ML Engineer & Researcher\n*Track your journey to mastery*",
            color=discord.Color.blue(),
            timestamp=now()
        )
        
        users = self.state.get_all_users()
        
        if not users:
            embed.description = "No user data yet. Start logging your learning!"
            embed.set_footer(text="Auto-refreshes every 5 minutes")
            return embed
        
        for user_data in users:
            user_id = user_data.get("user_id")
            username = user_data.get("username", "Unknown")
            
            try:
                discord_user = await self.bot.fetch_user(user_id)
                display_name = discord_user.display_name if discord_user else username
            except:
                display_name = username
            
            # Get stats
            points = user_data.get("points", 0)
            streak = user_data.get("streak", 0)
            max_streak = user_data.get("max_streak", 0)
            days_active = user_data.get("days_active", 0)
            total_logs = user_data.get("total_logs", 0)
            skill_level = user_data.get("skill_level", 0)
            health = user_data.get("streak_health", "safe")
            
            # Get career pathway info
            progress = get_progress_summary(user_data)
            current_milestone = progress["current_milestone"]
            next_milestone = progress["next_milestone"]
            
            level_info = config.SKILL_LEVELS.get(skill_level, {})
            level_emoji = level_info.get("emoji", "🌱")
            level_name = level_info.get("name", "Beginner")
            
            health_emoji = {"safe": "🟢", "at-risk": "🟡", "broken": "🔴"}.get(health, "⚪")
            streak_emoji = get_streak_status_emoji(streak)
            
            # Create progress bar for career pathway
            progress_pct = progress["progress_percentage"]
            progress_bar = "█" * int(progress_pct // 10) + "░" * (10 - int(progress_pct // 10))
            
            # Topic coverage
            coverage = user_data.get("topic_coverage", {})
            coverage_str = " ".join(
                f"{t}:{int(v)}" for t, v in coverage.items() if v > 0
            ) or "None yet"
            
            # Badges
            badges = user_data.get("badges", [])
            badge_str = " ".join(
                config.BADGES.get(b, {}).get("emoji", "")
                for b in badges[:5]
            ) or "None"
            
            # Build pathway status
            pathway_status = f"{current_milestone['emoji']} **{current_milestone['name']}**"
            if next_milestone:
                points_needed = next_milestone["points_range"][0] - points
                pathway_status += f"\n[{progress_bar}] {progress_pct:.0f}%"
                pathway_status += f"\n{points_needed:,} pts → {next_milestone['name']}"
            else:
                pathway_status += "\n✨ Maximum level achieved!"
            
            # Create user section
            user_stats = (
                f"🎖️ {level_emoji} **{level_name}** | {health_emoji} Streak: {streak_emoji} **{streak}** days (best: {max_streak})\n"
                f"💰 **{points:,}** pts | 📝 **{total_logs}** logs | 📅 **{days_active}** days active\n\n"
                f"**Career Path Progress:**\n{pathway_status}\n\n"
                f"📚 Topics: {coverage_str}\n"
                f"🏆 Badges: {badge_str}"
            )
            
            embed.add_field(
                name=f"👤 {display_name}",
                value=user_stats,
                inline=False
            )
        
        # Add general info
        embed.add_field(
            name="💡 Quick Commands",
            value="`/stats` • `/ask` • `/mystatus` • `/streak` • `/leaderboard`",
            inline=False
        )
        
        # Add last update time
        embed.set_footer(text=f"Auto-refreshes every {config.DASHBOARD_REFRESH_SECONDS // 60} min | Last update")
        
        return embed
    
    async def _post_evaluation(self, user_id: int, result) -> None:
        """Post evaluation results to the dashboard channel."""
        try:
            channel = self.bot.get_channel(config.DASHBOARD_CHANNEL_ID)
            if not channel:
                channel = await self.bot.fetch_channel(config.DASHBOARD_CHANNEL_ID)
            
            if not channel:
                return
            
            discord_user = await self.bot.fetch_user(user_id)
            if not discord_user:
                return
            
            embed = self.evaluator.create_evaluation_embed(result, discord_user)
            
            await channel.send(
                content=f"📋 Daily evaluation for {discord_user.mention}",
                embed=embed
            )
            
        except Exception as e:
            logger.error(f"Error posting evaluation: {e}")
    
    # Slash Commands
    
    @discord.slash_command(
        name="stats",
        description="View your personal learning statistics"
    )
    async def stats_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to view stats for (default: yourself)",
            required=False
        )
    ) -> None:
        """Display personal stats."""
        target_user = user or ctx.author
        
        if target_user.id not in config.USER_IDS:
            await ctx.respond("❌ This user is not being tracked.", ephemeral=True)
            return
        
        user_data = self.state.get_user(target_user.id)
        if not user_data:
            await ctx.respond("❌ User data not found.", ephemeral=True)
            return
        
        embed = await self._create_stats_embed(target_user, user_data)
        await ctx.respond(embed=embed)
    
    async def _create_stats_embed(
        self,
        user: discord.User,
        user_data: dict
    ) -> discord.Embed:
        """Create detailed stats embed for a user."""
        skill_level = user_data.get("skill_level", 0)
        level_info = config.SKILL_LEVELS.get(skill_level, {})
        
        # Calculate progress to next level
        current_points = user_data.get("points", 0)
        next_level = skill_level + 1
        
        if next_level in config.SKILL_LEVELS:
            next_level_info = config.SKILL_LEVELS[next_level]
            points_needed = next_level_info["min_points"] - current_points
            current_min = level_info.get("min_points", 0)
            next_min = next_level_info["min_points"]
            progress = ((current_points - current_min) / (next_min - current_min)) * 100
            progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
            level_progress = f"[{progress_bar}] {progress:.1f}%\n{points_needed:,} pts to {next_level_info['name']}"
        else:
            level_progress = "🎉 Maximum level reached!"
        
        embed = discord.Embed(
            title=f"📈 Stats for {user.display_name}",
            description=f"{level_info.get('emoji', '')} **{level_info.get('name', 'Beginner')}**",
            color=discord.Color.green(),
            timestamp=now()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url if user.display_avatar else None)
        
        # Main stats
        embed.add_field(
            name="💰 Total Points",
            value=f"**{user_data.get('points', 0):,}**",
            inline=True
        )
        
        streak = user_data.get("streak", 0)
        embed.add_field(
            name=f"{get_streak_status_emoji(streak)} Current Streak",
            value=f"**{streak}** days",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Best Streak",
            value=f"**{user_data.get('max_streak', 0)}** days",
            inline=True
        )
        
        embed.add_field(
            name="📝 Total Logs",
            value=f"**{user_data.get('total_logs', 0)}**",
            inline=True
        )
        
        embed.add_field(
            name="📅 Days Active",
            value=f"**{user_data.get('days_active', 0)}**",
            inline=True
        )
        
        embed.add_field(
            name="🔬 Evaluations",
            value=f"**{user_data.get('evaluation_count', 0)}**",
            inline=True
        )
        
        # Level progress
        embed.add_field(
            name="📊 Level Progress",
            value=level_progress,
            inline=False
        )
        
        # Topic coverage
        coverage = user_data.get("topic_coverage", {})
        if coverage:
            total = sum(coverage.values())
            if total > 0:
                coverage_str = "\n".join(
                    f"{'🤖' if t == 'AI' else '📈' if t == 'ML' else '🧠' if t == 'DL' else '📊'} "
                    f"**{t}**: {v:.0f} ({(v/total)*100:.0f}%)"
                    for t, v in coverage.items()
                )
            else:
                coverage_str = "No topics covered yet"
        else:
            coverage_str = "No topics covered yet"
        
        embed.add_field(
            name="📚 Topic Coverage",
            value=coverage_str,
            inline=False
        )
        
        # Top concepts
        concept_freq = user_data.get("concept_frequency", {})
        if concept_freq:
            top_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            concepts_str = ", ".join(f"`{c}` ({n})" for c, n in top_concepts)
        else:
            concepts_str = "None tracked yet"
        
        embed.add_field(
            name="🧪 Top Concepts",
            value=concepts_str,
            inline=False
        )
        
        # Badges
        badges = user_data.get("badges", [])
        if badges:
            badge_strs = []
            for badge_id in badges:
                badge = config.BADGES.get(badge_id, {})
                badge_strs.append(f"{badge.get('emoji', '🏅')} {badge.get('name', badge_id)}")
            badges_str = "\n".join(badge_strs)
        else:
            badges_str = "No badges earned yet"
        
        embed.add_field(
            name="🎖️ Badges",
            value=badges_str,
            inline=False
        )
        
        # Last evaluation
        last_eval = user_data.get("last_evaluation")
        if last_eval:
            analysis = last_eval.get("analysis", {})
            embed.add_field(
                name="📋 Last Evaluation",
                value=(
                    f"Focus: {analysis.get('primary_focus', 'N/A')} | "
                    f"Depth: {analysis.get('depth_score', 'N/A')}/10\n"
                    f"Points: +{last_eval.get('points_earned', 0)}"
                ),
                inline=False
            )
        
        embed.set_footer(text=f"Member since {user_data.get('created_at', 'Unknown')}")
        
        return embed
    
    @discord.slash_command(
        name="leaderboard",
        description="View the learning leaderboard"
    )
    async def leaderboard_command(self, ctx: discord.ApplicationContext) -> None:
        """Display the leaderboard."""
        users = self.state.get_all_users()
        
        if not users:
            await ctx.respond("No users found.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Learning Leaderboard",
            description="Who's leading the AI/ML learning journey?",
            color=discord.Color.gold(),
            timestamp=now()
        )
        
        # Sort by points
        sorted_users = sorted(users, key=lambda x: x.get("points", 0), reverse=True)
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(sorted_users):
            user_id = user_data.get("user_id")
            
            try:
                discord_user = await self.bot.fetch_user(user_id)
                display_name = discord_user.display_name if discord_user else user_data.get("username", "Unknown")
            except:
                display_name = user_data.get("username", "Unknown")
            
            medal = medals[i] if i < len(medals) else f"#{i+1}"
            
            points = user_data.get("points", 0)
            streak = user_data.get("streak", 0)
            level = config.SKILL_LEVELS.get(user_data.get("skill_level", 0), {})
            
            embed.add_field(
                name=f"{medal} {display_name}",
                value=(
                    f"💰 **{points:,}** pts | "
                    f"{get_streak_status_emoji(streak)} **{streak}** days | "
                    f"{level.get('emoji', '')} {level.get('name', 'Beginner')}"
                ),
                inline=False
            )
        
        # Motivational note
        embed.set_footer(text="Keep learning! Every log counts towards mastery.")
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="summary",
        description="Get your weekly AI mentor summary"
    )
    async def summary_command(self, ctx: discord.ApplicationContext) -> None:
        """Generate weekly summary."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        await ctx.defer()
        
        summary = await self.evaluator.get_weekly_summary(ctx.author.id)
        
        if not summary:
            await ctx.respond("❌ Could not generate summary.")
            return
        
        if summary.get("_empty"):
            await ctx.respond(summary.get("message", "No data this week."))
            return
        
        # Create summary embed
        rating_colors = {
            "A": discord.Color.gold(),
            "B": discord.Color.green(),
            "C": discord.Color.blue(),
            "D": discord.Color.orange(),
            "F": discord.Color.red()
        }
        
        rating = summary.get("week_rating", "C")
        
        embed = discord.Embed(
            title=f"📊 Weekly Summary - Grade: {rating}",
            description=summary.get("weekly_feedback", "Keep learning!"),
            color=rating_colors.get(rating, discord.Color.blue()),
            timestamp=now()
        )
        
        embed.add_field(
            name="📈 Concepts Learned",
            value=str(summary.get("total_concepts_learned", 0)),
            inline=True
        )
        
        embed.add_field(
            name="💪 Strongest Area",
            value=summary.get("strongest_area", "N/A"),
            inline=True
        )
        
        embed.add_field(
            name="📚 Focus Area",
            value=summary.get("weakest_area", "N/A"),
            inline=True
        )
        
        embed.add_field(
            name="📊 Consistency",
            value=summary.get("consistency_trend", "stable").title(),
            inline=True
        )
        
        embed.add_field(
            name="🔬 Depth Trend",
            value=summary.get("depth_trend", "stable").title(),
            inline=True
        )
        
        # Goals
        goals = summary.get("goals_for_next_week", [])
        if goals:
            goals_str = "\n".join(f"• {goal}" for goal in goals[:3])
            embed.add_field(
                name="🎯 Goals for Next Week",
                value=goals_str,
                inline=False
            )
        
        # Celebration
        if summary.get("celebration"):
            embed.add_field(
                name="🎉 Celebration",
                value=summary["celebration"],
                inline=False
            )
        
        if summary.get("_fallback"):
            embed.set_footer(text="⚠️ Generated with fallback (AI unavailable)")
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="badges",
        description="View all available badges and your progress"
    )
    async def badges_command(self, ctx: discord.ApplicationContext) -> None:
        """Display badge collection."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        user_data = self.state.get_user(ctx.author.id)
        if not user_data:
            await ctx.respond("❌ User data not found.", ephemeral=True)
            return
        
        earned_badges = set(user_data.get("badges", []))
        
        embed = discord.Embed(
            title="🏅 Badge Collection",
            description=f"You've earned **{len(earned_badges)}** of **{len(config.BADGES)}** badges!",
            color=discord.Color.purple(),
            timestamp=now()
        )
        
        for badge_id, badge_info in config.BADGES.items():
            emoji = badge_info.get("emoji", "🏅")
            name = badge_info.get("name", badge_id)
            desc = badge_info.get("description", "")
            
            if badge_id in earned_badges:
                status = "✅ Earned"
                field_name = f"{emoji} {name}"
            else:
                status = "🔒 Locked"
                field_name = f"⬜ {name}"
            
            embed.add_field(
                name=field_name,
                value=f"{desc}\n*{status}*",
                inline=True
            )
        
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot) -> None:
    """Setup function for the cog."""
    # This will be called from bot.py with proper dependencies
    pass
