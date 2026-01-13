#!/usr/bin/env python3
"""
AI Learning Mentor Bot
A Discord bot that helps users track and improve their AI/ML learning journey.

Features:
- Discord-native state storage (no external database)
- Daily learning log tracking
- Streak management with timezone support
- Gemini AI-powered evaluations and feedback
- Gamification with points, badges, and skill levels
- Competitive leaderboard
- Weekly AI mentor summaries
"""

import discord
from discord.ext import commands
import asyncio
import logging
import sys
import os
from datetime import datetime

from config import config
from services.discord_state import DiscordStateManager
from services.evaluator import init_evaluator
from services.gemini import gemini_service
from cogs.tracking import TrackingCog
from cogs.dashboard import DashboardCog
from cogs.admin import AdminCog
from utils import format_datetime, now


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

# Reduce noise from discord.py
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class LearningMentorBot(discord.Bot):
    """
    Main bot class for AI Learning Mentor.
    """
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            intents=intents,
            debug_guilds=[config.GUILD_ID] if config.GUILD_ID else None,
            auto_sync_commands=True  # Ensure commands sync on startup
        )
        
        self.state_manager: DiscordStateManager = None
        self.evaluator = None
        self._startup_time = None
        self._ready_once = False  # Track if on_ready has fired
    
    async def on_ready(self) -> None:
        """Called when bot is ready."""
        # Prevent duplicate initialization on reconnect
        if self._ready_once:
            logger.info(f"Bot reconnected as {self.user.name}")
            return
        
        self._startup_time = now()
        self._ready_once = True
        
        logger.info(f"{'='*60}")
        logger.info(f"Bot connected as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"{'='*60}")
        
        # Verify guild access
        guild = self.get_guild(config.GUILD_ID)
        if not guild:
            logger.error(f"Cannot access guild {config.GUILD_ID}! Bot may not be in the server.")
            await self.close()
            return
        
        logger.info(f"Found guild: {guild.name}")
        
        # Initialize state manager
        logger.info("Initializing state manager...")
        self.state_manager = DiscordStateManager(self)
        success = await self.state_manager.initialize()
        
        if not success:
            logger.error("Failed to initialize state manager!")
            await self.close()
            return
        
        logger.info("State manager initialized successfully")
        
        # Initialize evaluator
        logger.info("Initializing evaluator...")
        self.evaluator = init_evaluator(self, self.state_manager)
        logger.info("Evaluator initialized")
        
        # Load cogs
        logger.info("Loading cogs...")
        await self._load_cogs()
        
        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your learning journey 📚"
            ),
            status=discord.Status.online
        )
        
        logger.info("Bot is ready!")
        logger.info(f"{'='*60}")
    
    async def _load_cogs(self) -> None:
        """Load all cogs."""
        try:
            # Create cog instances with dependencies
            tracking_cog = TrackingCog(self, self.state_manager, self.evaluator)
            dashboard_cog = DashboardCog(self, self.state_manager, self.evaluator)
            admin_cog = AdminCog(self, self.state_manager, self.evaluator)
            
            # Add cogs
            self.add_cog(tracking_cog)
            self.add_cog(dashboard_cog)
            self.add_cog(admin_cog)
            
            logger.info(f"Loaded {len(self.cogs)} cogs: {', '.join(self.cogs.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading cogs: {e}")
            raise
    
    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Handle errors in event handlers."""
        logger.exception(f"Error in {event_method}")
    
    async def on_disconnect(self) -> None:
        """Called when bot disconnects."""
        logger.warning("Bot disconnected from Discord!")
    
    async def on_resumed(self) -> None:
        """Called when bot resumes session."""
        logger.info("Bot resumed connection to Discord")
    
    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        error: discord.DiscordException
    ) -> None:
        """Handle errors in slash commands."""
        if isinstance(error, commands.CheckFailure):
            await ctx.respond(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                f"⏳ Command on cooldown. Try again in {error.retry_after:.1f}s",
                ephemeral=True
            )
        else:
            logger.exception(f"Command error in {ctx.command}: {error}")
            await ctx.respond(
                "❌ An error occurred while processing your command.",
                ephemeral=True
            )
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when bot joins a guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when bot is removed from a guild."""
        logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
    
    async def close(self) -> None:
        """Clean shutdown."""
        logger.info("Shutting down...")
        
        # Close Gemini session
        await gemini_service.close()
        
        # Save state one last time
        if self.state_manager:
            await self.state_manager.save(create_backup=True)
        
        await super().close()
        logger.info("Shutdown complete")
    
    def get_uptime(self) -> str:
        """Get bot uptime as formatted string."""
        if not self._startup_time:
            return "Unknown"
        
        delta = now() - self._startup_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m {seconds}s"


def validate_config() -> bool:
    """Validate configuration before starting."""
    errors = config.validate()
    
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    return True


def main() -> None:
    """Main entry point."""
    logger.info("Starting AI Learning Mentor Bot...")
    logger.info(f"Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    
    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Please check your .env file.")
        sys.exit(1)
    
    logger.info("Configuration validated")
    logger.info(f"Guild ID: {config.GUILD_ID}")
    logger.info(f"Tracking {len(config.USER_IDS)} user(s)")
    logger.info(f"Timezone: {config.TIMEZONE}")
    
    # Create and run bot
    bot = LearningMentorBot()
    
    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token!")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    main()
