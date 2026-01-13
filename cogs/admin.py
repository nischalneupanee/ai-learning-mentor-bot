"""
Admin Cog - Administrative commands and utilities.
"""

import discord
from discord.ext import commands
import asyncio
import logging
from typing import Optional

from config import config
from services.discord_state import DiscordStateManager
from services.evaluator import Evaluator
from services.gemini import gemini_service
from utils import (
    now,
    today,
    format_datetime,
    safe_json_dumps,
    compress_for_storage,
)

logger = logging.getLogger(__name__)


def is_admin():
    """Check if user has admin permissions."""
    async def predicate(ctx: discord.ApplicationContext) -> bool:
        if not ctx.guild:
            return False
        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            return False
        return member.guild_permissions.administrator
    return commands.check(predicate)


class AdminCog(commands.Cog):
    """Cog for administrative commands."""
    
    def __init__(
        self,
        bot: discord.Bot,
        state_manager: DiscordStateManager,
        evaluator: Evaluator
    ):
        self.bot = bot
        self.state = state_manager
        self.evaluator = evaluator
    
    admin_group = discord.SlashCommandGroup(
        name="admin",
        description="Administrative commands",
        default_member_permissions=discord.Permissions(administrator=True)
    )
    
    @admin_group.command(
        name="reset_day",
        description="Reset daily flags for all users"
    )
    @is_admin()
    async def reset_day_command(self, ctx: discord.ApplicationContext) -> None:
        """Reset daily flags."""
        await ctx.defer(ephemeral=True)
        
        try:
            # Clear today's daily flags
            state = self.state._state
            date_key = today()
            
            if "daily_flags" in state and date_key in state["daily_flags"]:
                del state["daily_flags"][date_key]
                await self.state.save()
            
            await ctx.respond("✅ Daily flags reset successfully.", ephemeral=True)
            logger.info(f"Admin {ctx.author.id} reset daily flags")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error resetting day: {e}")
    
    @admin_group.command(
        name="recalculate_stats",
        description="Recalculate stats for a user"
    )
    @is_admin()
    async def recalculate_stats_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to recalculate stats for",
            required=True
        )
    ) -> None:
        """Recalculate user stats from message history."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            # Collect all logs
            from utils import get_last_n_days, analyze_message, clean_message_content
            
            total_points = 0
            total_logs = 0
            all_concepts = []
            topic_coverage = {"AI": 0, "ML": 0, "DL": 0, "DS": 0}
            
            learning_channel = self.bot.get_channel(config.LEARNING_CHANNEL_ID)
            
            if learning_channel:
                async for message in learning_channel.history(limit=1000):
                    if message.author.id != user.id:
                        continue
                    
                    if message.author.bot:
                        continue
                    
                    content = clean_message_content(message.content)
                    analysis = analyze_message(content)
                    
                    if analysis["qualifies"]:
                        total_logs += 1
                        total_points += config.BASE_POINTS
                        
                        if analysis["depth_score"] >= 3:
                            total_points += config.DEPTH_BONUS
                        
                        all_concepts.extend(analysis.get("concepts", []))
                        
                        topic = analysis.get("primary_topic", "Mixed")
                        if topic in topic_coverage:
                            topic_coverage[topic] += 1
            
            # Build concept frequency
            concept_freq = {}
            for concept in all_concepts:
                concept_freq[concept] = concept_freq.get(concept, 0) + 1
            
            # Update user
            await self.state.update_user(user.id, {
                "points": total_points,
                "total_logs": total_logs,
                "concept_frequency": concept_freq,
                "topic_coverage": topic_coverage,
            })
            
            # Update skill level
            await self.state.update_skill_level(user.id)
            
            await ctx.respond(
                f"✅ Recalculated stats for {user.mention}:\n"
                f"• Points: {total_points}\n"
                f"• Logs: {total_logs}\n"
                f"• Concepts: {len(concept_freq)}",
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} recalculated stats for {user.id}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error recalculating stats: {e}")
    
    @admin_group.command(
        name="force_evaluate",
        description="Force run evaluation for a user"
    )
    @is_admin()
    async def force_evaluate_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to evaluate",
            required=True
        )
    ) -> None:
        """Force evaluation for a user."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer()
        
        try:
            result = await self.evaluator.evaluate_user(user.id, force=True)
            
            if not result:
                await ctx.respond("❌ No logs found to evaluate or evaluation failed.")
                return
            
            embed = self.evaluator.create_evaluation_embed(result, user)
            await ctx.respond(embed=embed)
            
            logger.info(f"Admin {ctx.author.id} forced evaluation for {user.id}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}")
            logger.error(f"Error forcing evaluation: {e}")
    
    @admin_group.command(
        name="backup_state",
        description="Create a backup of current state"
    )
    @is_admin()
    async def backup_state_command(self, ctx: discord.ApplicationContext) -> None:
        """Create state backup."""
        await ctx.defer(ephemeral=True)
        
        try:
            success = await self.state.force_backup()
            
            if success:
                await ctx.respond("✅ State backup created successfully.", ephemeral=True)
            else:
                await ctx.respond("❌ Failed to create backup.", ephemeral=True)
            
            logger.info(f"Admin {ctx.author.id} created state backup")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error creating backup: {e}")
    
    @admin_group.command(
        name="health",
        description="Check bot health status"
    )
    @is_admin()
    async def health_command(self, ctx: discord.ApplicationContext) -> None:
        """Display bot health status."""
        await ctx.defer(ephemeral=True)
        
        try:
            # State health
            state_health = self.state.get_health_status()
            
            # Gemini health
            gemini_requests = {}
            for user_id in config.USER_IDS:
                gemini_requests[str(user_id)] = gemini_service.get_remaining_requests(user_id)
            
            # Bot health
            latency = round(self.bot.latency * 1000, 2)
            
            embed = discord.Embed(
                title="🏥 Bot Health Status",
                color=discord.Color.green() if state_health["initialized"] else discord.Color.red(),
                timestamp=now()
            )
            
            # State status
            embed.add_field(
                name="📦 State Manager",
                value=(
                    f"Initialized: {'✅' if state_health['initialized'] else '❌'}\n"
                    f"Version: {state_health.get('state_version', 'N/A')}\n"
                    f"Users: {state_health.get('user_count', 0)}\n"
                    f"Size: {state_health.get('state_size_bytes', 0):,} bytes\n"
                    f"Last Save: {state_health.get('last_save', 'N/A')}"
                ),
                inline=True
            )
            
            # Gemini status
            gemini_str = "\n".join(
                f"User {uid}: {remaining} remaining"
                for uid, remaining in gemini_requests.items()
            )
            embed.add_field(
                name="🤖 Gemini API",
                value=gemini_str or "No users",
                inline=True
            )
            
            # Bot status
            embed.add_field(
                name="🔌 Connection",
                value=(
                    f"Latency: {latency}ms\n"
                    f"Guilds: {len(self.bot.guilds)}\n"
                    f"Ready: {'✅' if self.bot.is_ready() else '❌'}"
                ),
                inline=True
            )
            
            # Channels
            channels_ok = all([
                self.bot.get_channel(config.STATE_CHANNEL_ID),
                self.bot.get_channel(config.LEARNING_CHANNEL_ID),
                self.bot.get_channel(config.DASHBOARD_CHANNEL_ID),
                self.bot.get_channel(config.DAILY_THREADS_CHANNEL_ID),
            ])
            
            embed.add_field(
                name="📢 Channels",
                value=(
                    f"State: {'✅' if self.bot.get_channel(config.STATE_CHANNEL_ID) else '❌'}\n"
                    f"Learning: {'✅' if self.bot.get_channel(config.LEARNING_CHANNEL_ID) else '❌'}\n"
                    f"Dashboard: {'✅' if self.bot.get_channel(config.DASHBOARD_CHANNEL_ID) else '❌'}\n"
                    f"Threads: {'✅' if self.bot.get_channel(config.DAILY_THREADS_CHANNEL_ID) else '❌'}"
                ),
                inline=True
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error checking health: {e}")
    
    @admin_group.command(
        name="simulate_day",
        description="Simulate a day with custom logs"
    )
    @is_admin()
    async def simulate_day_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to simulate for",
            required=True
        ),
        logs: discord.Option(
            str,
            description="Logs separated by | (pipe)",
            required=True
        )
    ) -> None:
        """Simulate a day with custom logs."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            log_list = [log.strip() for log in logs.split("|") if log.strip()]
            
            if not log_list:
                await ctx.respond("❌ No valid logs provided.", ephemeral=True)
                return
            
            result = await self.evaluator.simulate_day(user.id, log_list)
            
            if "error" in result:
                await ctx.respond(f"❌ Error: {result['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🔬 Simulation Results",
                description=f"Simulated {len(log_list)} logs for {user.mention}",
                color=discord.Color.blue(),
                timestamp=now()
            )
            
            embed.add_field(
                name="AI Analysis",
                value=f"Focus: {result.get('ai_analysis', {}).get('primary_focus', 'N/A')}\n"
                      f"Depth: {result.get('ai_analysis', {}).get('depth_score', 'N/A')}/10",
                inline=True
            )
            
            embed.add_field(
                name="Estimated Points",
                value=f"+{result.get('estimated_points', 0)} pts",
                inline=True
            )
            
            embed.add_field(
                name="Repetition Penalty",
                value=f"{result.get('repetition_penalty', 1.0):.2f}x",
                inline=True
            )
            
            if result.get("concepts_detected"):
                embed.add_field(
                    name="Concepts Detected",
                    value=", ".join(f"`{c}`" for c in result["concepts_detected"][:10]),
                    inline=False
                )
            
            if result.get("new_concepts"):
                embed.add_field(
                    name="New Concepts",
                    value=", ".join(f"`{c}`" for c in result["new_concepts"][:5]),
                    inline=True
                )
            
            if result.get("repeated_concepts"):
                embed.add_field(
                    name="Repeated Concepts",
                    value=", ".join(f"`{c}`" for c in result["repeated_concepts"][:5]),
                    inline=True
                )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
            logger.info(f"Admin {ctx.author.id} ran simulation for {user.id}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error in simulation: {e}")
    
    @admin_group.command(
        name="set_role",
        description="Set skill level role for a user"
    )
    @is_admin()
    async def set_role_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to set role for",
            required=True
        ),
        level: discord.Option(
            int,
            description="Skill level (0-3)",
            required=True,
            min_value=0,
            max_value=3
        )
    ) -> None:
        """Set skill level and assign corresponding role."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            # Update skill level in state
            await self.state.update_user(user.id, {"skill_level": level})
            
            level_info = config.SKILL_LEVELS.get(level, {})
            level_name = level_info.get("name", "Unknown")
            
            # Try to assign role if it exists
            if ctx.guild:
                member = ctx.guild.get_member(user.id)
                if member:
                    role = discord.utils.get(ctx.guild.roles, name=level_name)
                    if role:
                        # Remove other skill level roles
                        for lvl, info in config.SKILL_LEVELS.items():
                            old_role = discord.utils.get(ctx.guild.roles, name=info.get("name"))
                            if old_role and old_role in member.roles:
                                await member.remove_roles(old_role)
                        
                        await member.add_roles(role)
            
            await ctx.respond(
                f"✅ Set {user.mention}'s skill level to "
                f"{level_info.get('emoji', '')} **{level_name}**",
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} set {user.id} to level {level}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error setting role: {e}")
    
    @admin_group.command(
        name="view_state",
        description="View raw state JSON"
    )
    @is_admin()
    async def view_state_command(self, ctx: discord.ApplicationContext) -> None:
        """View current state."""
        await ctx.defer(ephemeral=True)
        
        try:
            state = self.state.state
            state_json = safe_json_dumps(state, compact=False)
            
            # Split if too long
            if len(state_json) > 1900:
                # Send as file
                import io
                file = discord.File(
                    io.BytesIO(state_json.encode('utf-8')),
                    filename=f"state_{today()}.json"
                )
                await ctx.respond("📦 State too large, attached as file:", file=file, ephemeral=True)
            else:
                await ctx.respond(f"```json\n{state_json}\n```", ephemeral=True)
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error viewing state: {e}")
    
    @admin_group.command(
        name="cleanup",
        description="Clean up old daily flags"
    )
    @is_admin()
    async def cleanup_command(
        self,
        ctx: discord.ApplicationContext,
        days: discord.Option(
            int,
            description="Days of flags to keep (default: 7)",
            required=False,
            default=7,
            min_value=1,
            max_value=30
        )
    ) -> None:
        """Clean up old data."""
        await ctx.defer(ephemeral=True)
        
        try:
            await self.state.cleanup_old_flags(keep_days=days)
            await ctx.respond(f"✅ Cleaned up flags older than {days} days.", ephemeral=True)
            
            logger.info(f"Admin {ctx.author.id} ran cleanup (keep {days} days)")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error in cleanup: {e}")
    
    @admin_group.command(
        name="award_badge",
        description="Manually award a badge to a user"
    )
    @is_admin()
    async def award_badge_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to award badge to",
            required=True
        ),
        badge_id: discord.Option(
            str,
            description="Badge ID to award",
            required=True,
            choices=[
                discord.OptionChoice(name=v["name"], value=k)
                for k, v in config.BADGES.items()
            ]
        )
    ) -> None:
        """Manually award a badge."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            awarded = await self.state.award_badge(user.id, badge_id)
            
            badge_info = config.BADGES.get(badge_id, {})
            
            if awarded:
                await ctx.respond(
                    f"✅ Awarded {badge_info.get('emoji', '🏅')} "
                    f"**{badge_info.get('name', badge_id)}** to {user.mention}!",
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    f"ℹ️ {user.mention} already has this badge.",
                    ephemeral=True
                )
            
            logger.info(f"Admin {ctx.author.id} awarded badge {badge_id} to {user.id}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error awarding badge: {e}")
    
    @admin_group.command(
        name="set_points",
        description="Manually set points for a user"
    )
    @is_admin()
    async def set_points_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to set points for",
            required=True
        ),
        points: discord.Option(
            int,
            description="Points to set",
            required=True,
            min_value=0
        )
    ) -> None:
        """Manually set user points."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            await self.state.update_user(user.id, {"points": points})
            await self.state.update_skill_level(user.id)
            
            await ctx.respond(
                f"✅ Set {user.mention}'s points to **{points:,}**",
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} set {user.id} points to {points}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error setting points: {e}")
    
    @admin_group.command(
        name="set_streak",
        description="Manually set streak for a user"
    )
    @is_admin()
    async def set_streak_command(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.User,
            description="User to set streak for",
            required=True
        ),
        streak: discord.Option(
            int,
            description="Streak to set",
            required=True,
            min_value=0
        )
    ) -> None:
        """Manually set user streak."""
        if user.id not in config.USER_IDS:
            await ctx.respond("❌ User is not tracked.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        try:
            user_data = self.state.get_user(user.id)
            max_streak = max(user_data.get("max_streak", 0), streak) if user_data else streak
            
            await self.state.update_user(user.id, {
                "streak": streak,
                "max_streak": max_streak,
                "streak_health": "safe" if streak > 0 else "broken",
                "last_log_date": today() if streak > 0 else None
            })
            
            await ctx.respond(
                f"✅ Set {user.mention}'s streak to **{streak}** days",
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} set {user.id} streak to {streak}")
            
        except Exception as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"Error setting streak: {e}")
    
    @admin_group.command(
        name="setup_channels",
        description="🚀 Auto-create all required channels for the bot"
    )
    @is_admin()
    async def setup_channels_command(self, ctx: discord.ApplicationContext) -> None:
        """Automatically create all required channels."""
        await ctx.defer(ephemeral=True)
        
        try:
            guild = ctx.guild
            created_channels = []
            
            # Define channels to create
            channels_to_create = [
                {
                    'name': '🤖-bot-state',
                    'purpose': 'Bot state storage (DO NOT DELETE)',
                    'type': 'STATE_CHANNEL_ID'
                },
                {
                    'name': '📚-learning-logs',
                    'purpose': 'Post your daily learning here',
                    'type': 'LEARNING_CHANNEL_ID'
                },
                {
                    'name': '📊-dashboard',
                    'purpose': 'Live stats dashboard',
                    'type': 'DASHBOARD_CHANNEL_ID'
                },
                {
                    'name': '📅-daily-threads',
                    'purpose': 'Daily learning threads for each user',
                    'type': 'DAILY_THREADS_CHANNEL_ID'
                }
            ]
            
            setup_instructions = "**✅ Channels Created!**\n\n"
            
            for channel_info in channels_to_create:
                # Check if channel already exists
                existing = discord.utils.get(guild.text_channels, name=channel_info['name'])
                
                if existing:
                    setup_instructions += f"• {existing.mention} - Already exists\n"
                else:
                    # Create channel
                    new_channel = await guild.create_text_channel(
                        name=channel_info['name'],
                        topic=channel_info['purpose']
                    )
                    created_channels.append(new_channel)
                    setup_instructions += f"• {new_channel.mention} - Created ✅\n"
            
            setup_instructions += f"\n**📋 Next Steps:**\n"
            setup_instructions += "1. Add these channel IDs to your `.env` file:\n"
            
            for channel_info in channels_to_create:
                channel = discord.utils.get(guild.text_channels, name=channel_info['name'])
                if channel:
                    setup_instructions += f"   `{channel_info['type']}={channel.id}`\n"
            
            setup_instructions += "\n2. Make sure `USER_IDS` is set in `.env`\n"
            setup_instructions += "3. Restart the bot\n"
            setup_instructions += "4. Run `/admin initialize_users`\n"
            
            embed = discord.Embed(
                title="🚀 Bot Setup Complete",
                description=setup_instructions,
                color=discord.Color.green(),
                timestamp=now()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            logger.info(f"Admin {ctx.author.id} ran setup_channels, created {len(created_channels)} channels")
            
        except Exception as e:
            await ctx.respond(f"❌ Error creating channels: {e}", ephemeral=True)
            logger.error(f"Error in setup_channels: {e}", exc_info=True)
    
    @admin_group.command(
        name="initialize_users",
        description="Initialize tracking for all configured users"
    )
    @is_admin()
    async def initialize_users_command(self, ctx: discord.ApplicationContext) -> None:
        """Initialize user tracking."""
        await ctx.defer(ephemeral=True)
        
        try:
            initialized_count = 0
            skipped_count = 0
            
            for user_id in config.USER_IDS:
                existing = self.state.get_user(user_id)
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Initialize user
                await self.state.update_user(user_id, {
                    "total_points": 0,
                    "current_streak": 0,
                    "best_streak": 0,
                    "total_logs": 0,
                    "concepts_learned": [],
                    "message_history": [],
                    "daily_thread_id": None,
                    "last_log_date": None
                })
                
                initialized_count += 1
            
            await ctx.respond(
                f"✅ Initialized {initialized_count} users, skipped {skipped_count} existing users.",
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} initialized {initialized_count} users")
            
        except Exception as e:
            await ctx.respond(f"❌ Error initializing users: {e}", ephemeral=True)
            logger.error(f"Error in initialize_users: {e}", exc_info=True)
    
    @admin_group.command(
        name="export_data",
        description="Export all bot data as JSON"
    )
    @is_admin()
    async def export_data_command(self, ctx: discord.ApplicationContext) -> None:
        """Export all data."""
        await ctx.defer(ephemeral=True)
        
        try:
            import json
            from io import BytesIO
            
            # Get full state
            full_state = self.state._state
            
            # Convert to JSON
            json_data = safe_json_dumps(full_state, indent=2)
            
            # Create file
            file_data = BytesIO(json_data.encode('utf-8'))
            file_name = f"bot_data_export_{today()}.json"
            
            discord_file = discord.File(file_data, filename=file_name)
            
            await ctx.respond(
                "📦 Here's your data export:",
                file=discord_file,
                ephemeral=True
            )
            
            logger.info(f"Admin {ctx.author.id} exported data")
            
        except Exception as e:
            await ctx.respond(f"❌ Error exporting data: {e}", ephemeral=True)
            logger.error(f"Error in export_data: {e}", exc_info=True)


def setup(bot: discord.Bot) -> None:
    """Setup function for the cog."""
    # This will be called from bot.py with proper dependencies
    pass
