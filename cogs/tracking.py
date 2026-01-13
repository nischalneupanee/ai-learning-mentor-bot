"""
Tracking Cog - Handles message tracking, streak management, and daily threads.
"""

import discord
from discord.ext import commands, tasks
from discord import SlashCommandGroup
import asyncio
import logging
from datetime import timedelta
from typing import Optional

from config import config
from services.discord_state import DiscordStateManager
from services.evaluator import Evaluator
from services.interactive_mentor import init_interactive_mentor
from utils import (
    analyze_message,
    get_effective_date,
    today,
    get_daily_thread_name,
    time_until_deadline,
    format_time_remaining,
    should_send_reminder,
    get_streak_status_emoji,
    is_same_day,
    now,
    format_datetime,
    clean_message_content,
)

logger = logging.getLogger(__name__)


class TrackingCog(commands.Cog):
    """Cog for tracking learning messages and managing streaks."""
    
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
        self._recent_messages: dict[int, list[str]] = {}  # user_id -> recent contents
        self._reminder_sent: dict[int, str] = {}  # user_id -> date of last reminder
        
        # Start tasks immediately
        try:
            self.daily_thread_task.start()
            self.streak_check_task.start()
            self.reminder_task.start()
            logger.info("TrackingCog: Tasks started in __init__")
        except Exception as e:
            logger.error(f"TrackingCog: Error starting tasks: {e}", exc_info=True)
    
    def cog_unload(self) -> None:
        """Called when cog is unloaded."""
        try:
            self.daily_thread_task.cancel()
            self.streak_check_task.cancel()
            self.reminder_task.cancel()
            logger.info("Tracking cog unloaded, tasks cancelled")
        except Exception as e:
            logger.error(f"Error stopping tracking tasks: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listen for learning log messages and mentor questions."""
        # Ignore bots
        if message.author.bot:
            return
        
        # Check if user is tracked
        if message.author.id not in config.USER_IDS:
            return
        
        # Check if it's a question for the mentor in daily thread
        if isinstance(message.channel, discord.Thread):
            if message.channel.parent_id == config.DAILY_THREADS_CHANNEL_ID:
                # Check if it's a question (contains ?)
                if await self._handle_mentor_question(message):
                    return  # Don't process as learning log if it's a question
        
        # Check if in valid channel
        valid_channels = [config.LEARNING_CHANNEL_ID]
        
        # Also check daily threads
        thread_id = self.state.get_daily_thread(message.author.id)
        if thread_id:
            valid_channels.append(thread_id)
        
        if message.channel.id not in valid_channels:
            # Check if it's a thread under daily threads channel
            if isinstance(message.channel, discord.Thread):
                if message.channel.parent_id == config.DAILY_THREADS_CHANNEL_ID:
                    pass  # Allow
                else:
                    return
            else:
                return
        
        # Process the message
        await self._process_learning_message(message)
    
    async def _handle_mentor_question(self, message: discord.Message) -> bool:
        """
        Handle questions to the AI mentor in daily threads.
        Returns True if message was handled as a question.
        """
        content = message.content.strip().lower()
        
        # Keywords that indicate a question to the mentor
        question_keywords = [
            "what should i", "how can i", "what is my", "should i",
            "recommend", "suggest", "help me", "what's next",
            "am i doing", "my progress", "my status", "how am i"
        ]
        
        # Check if it's a question
        is_question = "?" in content or any(keyword in content for keyword in question_keywords)
        
        if is_question and len(content) > 10:  # Meaningful question
            # Show typing indicator
            async with message.channel.typing():
                response = await self.mentor.answer_question(
                    message.author.id,
                    message.content
                )
                
                if response:
                    await message.reply(f"🤖 **AI Mentor:**\n\n{response}", mention_author=False)
                    return True
        
        return False
    
    async def _process_learning_message(self, message: discord.Message) -> None:
        """Process a potential learning log message."""
        user_id = message.author.id
        content = clean_message_content(message.content)
        
        # Get recent messages for duplicate check
        recent = self._recent_messages.get(user_id, [])
        
        # Analyze message
        analysis = analyze_message(content, recent)
        
        if not analysis["qualifies"]:
            logger.debug(f"Message from {user_id} did not qualify: {analysis['reason']}")
            return
        
        # Update recent messages cache
        recent.append(content)
        if len(recent) > 10:
            recent = recent[-10:]
        self._recent_messages[user_id] = recent
        
        # Calculate points
        points = config.BASE_POINTS
        if analysis["depth_score"] >= 3:  # Local depth score is 0-5
            points += config.DEPTH_BONUS
        
        # Update streak
        effective_date = get_effective_date()
        new_streak, health = await self.state.update_streak(
            user_id,
            effective_date,
            increment=True
        )
        
        # Add points
        total_points = await self.state.add_points(user_id, points)
        
        # Increment log count
        await self.state.increment_total_logs(user_id)
        
        # Update concepts
        if analysis["concepts"]:
            await self.state.update_concept_frequency(user_id, analysis["concepts"])
        
        # Check skill level
        new_level, level_changed = await self.state.update_skill_level(user_id)
        
        # React to message
        try:
            await message.add_reaction("✅")
            
            # Special reactions for milestones
            user = self.state.get_user(user_id)
            if user:
                total_logs = user.get("total_logs", 0)
                
                # Milestone reactions
                if total_logs == 1:
                    await message.add_reaction("🎉")
                elif total_logs % 50 == 0:
                    await message.add_reaction("💯")
                
                # Streak reactions
                if new_streak in [7, 14, 30, 50, 100]:
                    await message.add_reaction("🔥")
                
                # Level up notification
                if level_changed:
                    level_info = config.SKILL_LEVELS.get(new_level, {})
                    await message.channel.send(
                        f"🎊 **Level Up!** {message.author.mention} "
                        f"is now **{level_info.get('emoji', '')} {level_info.get('name', 'Unknown')}**!",
                        delete_after=30
                    )
        except discord.errors.Forbidden:
            logger.warning("Cannot add reaction - missing permissions")
        
        logger.info(
            f"Processed log from {user_id}: +{points} pts, "
            f"streak={new_streak}, depth={analysis['depth_score']}"
        )
    
    @tasks.loop(hours=1)
    async def daily_thread_task(self) -> None:
        """Create daily threads for users."""
        try:
            await self._ensure_daily_threads()
        except Exception as e:
            logger.error(f"Error in daily thread task: {e}", exc_info=True)
    
    @daily_thread_task.before_loop
    async def before_daily_thread_task(self) -> None:
        """Wait for bot to be ready."""
        try:
            await self.bot.wait_until_ready()
            # Small delay to let state initialize
            await asyncio.sleep(5)
            logger.info("TrackingCog: Creating initial daily threads...")
            # Create threads immediately on startup
            await self._ensure_daily_threads()
            logger.info("TrackingCog: Initial daily threads created")
        except Exception as e:
            logger.error(f"TrackingCog: Error in daily thread before_loop: {e}", exc_info=True)
    
    async def _ensure_daily_threads(self) -> None:
        """Ensure each user has a daily thread for today."""
        try:
            logger.debug("Ensuring daily threads...")
            channel = self.bot.get_channel(config.DAILY_THREADS_CHANNEL_ID)
            if not channel:
                logger.debug(f"Fetching channel {config.DAILY_THREADS_CHANNEL_ID}...")
                channel = await self.bot.fetch_channel(config.DAILY_THREADS_CHANNEL_ID)
            
            if not channel:
                logger.error(f"Daily threads channel {config.DAILY_THREADS_CHANNEL_ID} not found")
                return
            
            thread_name = get_daily_thread_name()
            current_date = today()
            logger.debug(f"Thread name: {thread_name}, Date: {current_date}")
            
            for user_id in config.USER_IDS:
                logger.debug(f"Checking thread for user {user_id}...")
                user = self.state.get_user(user_id)
                if not user:
                    logger.warning(f"User {user_id} not found in state")
                    continue
                
                # Check if we need a new thread
                existing_thread_id = user.get("daily_thread_id")
                need_new_thread = True
                
                if existing_thread_id:
                    logger.debug(f"Found existing thread ID {existing_thread_id} for user {user_id}")
                    try:
                        existing_thread = self.bot.get_channel(existing_thread_id)
                        if not existing_thread:
                            existing_thread = await self.bot.fetch_channel(existing_thread_id)
                        
                        # Check if thread is for today
                        if existing_thread and thread_name in existing_thread.name:
                            need_new_thread = False
                            logger.debug(f"Thread {existing_thread_id} is still valid for today")
                    except Exception as e:
                        logger.debug(f"Error checking existing thread: {e}")
                
                if need_new_thread:
                    logger.info(f"Creating new thread for user {user_id}")
                    await self._create_daily_thread(channel, user_id, user.get("username", f"User {user_id}"))
                else:
                    logger.debug(f"User {user_id} already has valid thread for today")
        
        except Exception as e:
            logger.error(f"Error in _ensure_daily_threads: {e}", exc_info=True)
    
    async def _create_daily_thread(
        self,
        channel: discord.TextChannel,
        user_id: int,
        username: str
    ) -> Optional[discord.Thread]:
        """Create a daily thread for a user."""
        try:
            thread_name = f"{get_daily_thread_name()} - {username}"
            logger.info(f"Creating thread: {thread_name}")
            
            # Create thread
            thread = await channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.public_thread,
                auto_archive_duration=1440  # 24 hours
            )
            
            logger.info(f"Thread created with ID {thread.id}")
            
            # Store thread ID
            await self.state.set_daily_thread(user_id, thread.id)
            logger.debug(f"Stored thread ID for user {user_id}")
            
            # Send welcome message
            user = await self.bot.fetch_user(user_id)
            user_data = self.state.get_user(user_id)
            
            streak = user_data.get("streak", 0) if user_data else 0
            streak_emoji = get_streak_status_emoji(streak)
            
            welcome_embed = discord.Embed(
                title=f"📚 Daily Learning Log",
                description=(
                    f"Good morning, {user.mention if user else username}! 🌅\n\n"
                    f"**Current Streak:** {streak_emoji} {streak} days\n"
                    f"**Deadline:** {format_time_remaining(time_until_deadline())}\n\n"
                    "Log your learning journey here today! Each quality entry earns points."
                ),
                color=discord.Color.blue(),
                timestamp=now()
            )
            
            welcome_embed.add_field(
                name="📝 Tips for Quality Logs",
                value=(
                    "• Explain what you learned in detail\n"
                    "• Include technical concepts and terms\n"
                    "• Reflect on challenges and insights\n"
                    "• Minimum 30 characters per entry"
                ),
                inline=False
            )
            
            await thread.send(embed=welcome_embed)
            
            logger.info(f"Created daily thread {thread.id} for user {user_id}")
            return thread
        
        except Exception as e:
            logger.error(f"Error creating daily thread for {user_id}: {e}")
            return None
    
    @tasks.loop(hours=1)
    async def streak_check_task(self) -> None:
        """Check and update streak health for all users."""
        try:
            await self.state.reset_daily_state()
            
            current_date = today()
            
            for user_id in config.USER_IDS:
                user = self.state.get_user(user_id)
                if not user:
                    continue
                
                last_log = user.get("last_log_date")
                current_streak = user.get("streak", 0)
                
                if not last_log:
                    continue
                
                # Check if streak is at risk
                if not is_same_day(last_log, current_date):
                    if user.get("streak_health") != "at-risk":
                        await self.state.update_user(user_id, {"streak_health": "at-risk"})
                        logger.info(f"User {user_id} streak now at-risk")
        
        except Exception as e:
            logger.error(f"Error in streak check task: {e}")
    
    @streak_check_task.before_loop
    async def before_streak_check_task(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()
    
    @tasks.loop(hours=2)
    async def reminder_task(self) -> None:
        """Send smart reminders to users at risk of losing streak."""
        try:
            for user_id in config.USER_IDS:
                user = self.state.get_user(user_id)
                if not user:
                    continue
                
                last_log = user.get("last_log_date")
                should_remind, reason = should_send_reminder(last_log)
                
                if not should_remind:
                    continue
                
                # Check if we already sent a reminder today
                last_reminder = self._reminder_sent.get(user_id)
                if last_reminder == today():
                    continue
                
                # Send reminder
                await self._send_streak_reminder(user_id, user, reason)
                self._reminder_sent[user_id] = today()
        
        except Exception as e:
            logger.error(f"Error in reminder task: {e}")
    
    @reminder_task.before_loop
    async def before_reminder_task(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()
    
    async def _send_streak_reminder(
        self,
        user_id: int,
        user_data: dict,
        reason: str
    ) -> None:
        """Send a streak reminder to user."""
        try:
            discord_user = await self.bot.fetch_user(user_id)
            if not discord_user:
                return
            
            streak = user_data.get("streak", 0)
            
            embed = discord.Embed(
                title="⏰ Streak Reminder",
                description=reason,
                color=discord.Color.orange(),
                timestamp=now()
            )
            
            embed.add_field(
                name="Current Streak",
                value=f"{get_streak_status_emoji(streak)} {streak} days",
                inline=True
            )
            
            embed.add_field(
                name="Time Remaining",
                value=format_time_remaining(time_until_deadline()),
                inline=True
            )
            
            embed.set_footer(text="Log something to keep your streak alive!")
            
            # Try to send to their daily thread first
            thread_id = self.state.get_daily_thread(user_id)
            if thread_id:
                try:
                    thread = await self.bot.fetch_channel(thread_id)
                    if thread:
                        await thread.send(
                            content=discord_user.mention,
                            embed=embed
                        )
                        return
                except:
                    pass
            
            # Fallback to DM
            try:
                await discord_user.send(embed=embed)
            except discord.errors.Forbidden:
                logger.warning(f"Cannot send DM to user {user_id}")
        
        except Exception as e:
            logger.error(f"Error sending streak reminder to {user_id}: {e}")
    
    # Slash Commands
    
    @discord.slash_command(
        name="streak",
        description="View your current streak status"
    )
    async def streak_command(self, ctx: discord.ApplicationContext) -> None:
        """Show streak status for user."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        user = self.state.get_user(ctx.author.id)
        if not user:
            await ctx.respond("❌ User data not found.", ephemeral=True)
            return
        
        streak = user.get("streak", 0)
        max_streak = user.get("max_streak", 0)
        health = user.get("streak_health", "safe")
        last_log = user.get("last_log_date", "Never")
        
        health_info = {
            "safe": ("🟢", "Safe", "You've logged today!"),
            "at-risk": ("🟡", "At Risk", "You haven't logged today yet!"),
            "broken": ("🔴", "Broken", "Your streak was reset.")
        }
        
        emoji, status, desc = health_info.get(health, ("⚪", "Unknown", ""))
        
        embed = discord.Embed(
            title=f"{get_streak_status_emoji(streak)} Streak Status",
            description=desc,
            color=discord.Color.green() if health == "safe" else 
                  discord.Color.orange() if health == "at-risk" else 
                  discord.Color.red()
        )
        
        embed.add_field(
            name="Current Streak",
            value=f"**{streak}** days",
            inline=True
        )
        
        embed.add_field(
            name="Best Streak",
            value=f"**{max_streak}** days",
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value=f"{emoji} {status}",
            inline=True
        )
        
        embed.add_field(
            name="Last Log",
            value=last_log or "Never",
            inline=True
        )
        
        embed.add_field(
            name="Time Until Deadline",
            value=format_time_remaining(time_until_deadline()),
            inline=True
        )
        
        # Streak milestones
        next_milestones = [7, 14, 30, 50, 100, 365]
        for milestone in next_milestones:
            if streak < milestone:
                days_to_go = milestone - streak
                embed.add_field(
                    name="Next Milestone",
                    value=f"🎯 {milestone} days ({days_to_go} to go)",
                    inline=True
                )
                break
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="ask",
        description="Ask your AI mentor anything about your learning journey"
    )
    async def ask_command(
        self,
        ctx: discord.ApplicationContext,
        question: discord.Option(
            str,
            description="Your question for the AI mentor",
            required=True
        )
    ) -> None:
        """Ask the AI mentor a question."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        await ctx.defer()
        
        # Get AI response
        response = await self.mentor.answer_question(ctx.author.id, question)
        
        embed = discord.Embed(
            title="🤖 AI Learning Mentor",
            description=response,
            color=discord.Color.blue(),
            timestamp=now()
        )
        
        embed.set_footer(text=f"Question from {ctx.author.display_name}")
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="mystatus",
        description="Get a comprehensive AI-generated status report"
    )
    async def mystatus_command(self, ctx: discord.ApplicationContext) -> None:
        """Get detailed status report with AI analysis."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        await ctx.defer()
        
        # Get status report from AI
        status = await self.mentor.get_status_report(ctx.author.id)
        
        if "error" in status:
            await ctx.respond(f"❌ {status['error']}")
            return
        
        # Create embed
        embed = discord.Embed(
            title="📊 Your Learning Status Report",
            description=status.get("overall_status", "No summary available"),
            color=discord.Color.green(),
            timestamp=now()
        )
        
        # Add strengths
        if status.get("strengths"):
            embed.add_field(
                name="💪 Strengths",
                value="\n".join(f"• {s}" for s in status["strengths"]),
                inline=False
            )
        
        # Add areas to improve
        if status.get("areas_to_improve"):
            embed.add_field(
                name="📈 Areas to Improve",
                value="\n".join(f"• {a}" for a in status["areas_to_improve"]),
                inline=False
            )
        
        # Add next steps
        if status.get("next_immediate_steps"):
            embed.add_field(
                name="🎯 Next Steps",
                value="\n".join(f"{i+1}. {s}" for i, s in enumerate(status["next_immediate_steps"])),
                inline=False
            )
        
        # Add pathway progress
        if "progress" in status:
            progress = status["progress"]
            current = progress["current_milestone"]
            embed.add_field(
                name="🗺️ Career Pathway",
                value=f"{current['name']} ({progress['progress_percentage']:.0f}%)",
                inline=True
            )
        
        # Add motivation
        if status.get("motivation_message"):
            embed.add_field(
                name="✨ Keep Going!",
                value=status["motivation_message"],
                inline=False
            )
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="goal",
        description="Get AI-generated learning trajectory and goals"
    )
    async def goal_command(self, ctx: discord.ApplicationContext) -> None:
        """Generate personalized learning goals."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        await ctx.defer()
        
        user = self.state.get_user(ctx.author.id)
        if not user:
            await ctx.respond("❌ User data not found.")
            return
        
        # Get recent evaluations
        recent_evals = list(self.state.get_cached_evaluations(ctx.author.id, 7).values())
        
        from services.gemini import gemini_service
        trajectory = await gemini_service.generate_goal_trajectory(user, recent_evals)
        
        embed = discord.Embed(
            title="🎯 Your Learning Trajectory",
            description=trajectory,
            color=discord.Color.purple()
        )
        
        level_info = config.SKILL_LEVELS.get(user.get("skill_level", 0), {})
        embed.set_footer(
            text=f"Current Level: {level_info.get('emoji', '')} {level_info.get('name', 'Beginner')}"
        )
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(
        name="export",
        description="Export your learning logs as a text file"
    )
    async def export_command(
        self,
        ctx: discord.ApplicationContext,
        days: discord.Option(
            int,
            description="Number of days to export (default: 7)",
            required=False,
            default=7,
            min_value=1,
            max_value=30
        )
    ) -> None:
        """Export user's learning logs."""
        if ctx.author.id not in config.USER_IDS:
            await ctx.respond("❌ You're not a tracked user.", ephemeral=True)
            return
        
        await ctx.defer()
        
        # Collect logs
        from utils import get_last_n_days
        all_logs = []
        
        for date in get_last_n_days(days):
            logs = await self.evaluator.collect_daily_logs(ctx.author.id, date)
            if logs:
                all_logs.append(f"\n{'='*50}\n📅 {date}\n{'='*50}\n")
                for content, timestamp in logs:
                    all_logs.append(f"\n[{timestamp.strftime('%H:%M')}]\n{content}\n")
        
        if not all_logs:
            await ctx.respond("No logs found for the specified period.")
            return
        
        # Create text file
        content = f"Learning Log Export for {ctx.author.name}\n"
        content += f"Exported: {format_datetime(now())}\n"
        content += f"Period: Last {days} days\n"
        content += "\n".join(all_logs)
        
        # Send as attachment
        import io
        file = discord.File(
            io.BytesIO(content.encode('utf-8')),
            filename=f"learning_logs_{ctx.author.name}_{today()}.txt"
        )
        
        await ctx.respond(
            content=f"📦 Here are your learning logs for the last {days} days!",
            file=file
        )


def setup(bot: discord.Bot) -> None:
    """Setup function for the cog."""
    # This will be called from bot.py with proper dependencies
    pass
