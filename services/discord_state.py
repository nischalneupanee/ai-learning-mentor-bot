"""
Discord-native state management service.
Uses pinned embeds and locked threads as the database.
"""

import discord
import asyncio
import logging
from typing import Optional, Any
from datetime import datetime

from config import config, DEFAULT_STATE, get_default_user_state
from utils import (
    safe_json_loads,
    safe_json_dumps,
    compress_for_storage,
    decompress_from_storage,
    validate_state_structure,
    merge_dicts,
    safe_get,
    safe_set,
    now,
    today,
    format_datetime,
    truncate_for_embed,
)

logger = logging.getLogger(__name__)


class DiscordStateManager:
    """
    Manages bot state using Discord as the database.
    
    Primary storage: Pinned embed in STATE_CHANNEL
    Backup storage: Locked thread in STATE_CHANNEL
    """
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self._state: dict = {}
        self._state_message_id: Optional[int] = None
        self._backup_thread_id: Optional[int] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._last_save = None
    
    @property
    def state(self) -> dict:
        """Get current state (read-only access)."""
        return self._state.copy()
    
    async def initialize(self) -> bool:
        """
        Initialize state from Discord.
        Loads from pinned embed or creates new state.
        """
        async with self._lock:
            try:
                channel = self.bot.get_channel(config.STATE_CHANNEL_ID)
                if not channel:
                    channel = await self.bot.fetch_channel(config.STATE_CHANNEL_ID)
                
                if not channel:
                    logger.error("State channel not found")
                    return False
                
                # Try to find pinned state message
                pins = await channel.pins()
                state_message = None
                
                for pin in pins:
                    if pin.author.id == self.bot.user.id and pin.embeds:
                        embed = pin.embeds[0]
                        if embed.title == "🔒 Bot State [DO NOT MODIFY]":
                            state_message = pin
                            break
                
                if state_message:
                    # Load existing state
                    self._state_message_id = state_message.id
                    state_json = state_message.embeds[0].description
                    self._state = decompress_from_storage(state_json)
                    
                    # Validate and migrate if needed
                    await self._validate_and_migrate()
                    logger.info(f"Loaded state from message {state_message.id}")
                else:
                    # Create new state
                    self._state = DEFAULT_STATE.copy()
                    self._state["bot_metadata"]["started_at"] = format_datetime(now())
                    self._state["last_updated"] = format_datetime(now())
                    
                    # Initialize users
                    for user_id in config.USER_IDS:
                        try:
                            user = await self.bot.fetch_user(user_id)
                            username = user.name if user else f"User_{user_id}"
                        except:
                            username = f"User_{user_id}"
                        
                        self._state["users"][str(user_id)] = get_default_user_state(
                            user_id, username
                        )
                        self._state["users"][str(user_id)]["created_at"] = format_datetime(now())
                    
                    # Create and pin state message
                    await self._create_state_message(channel)
                    logger.info("Created new state")
                
                # Find or create backup thread
                await self._setup_backup_thread(channel)
                
                self._initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize state: {e}")
                return False
    
    async def _validate_and_migrate(self) -> None:
        """Validate state structure and migrate if needed."""
        is_valid, errors = validate_state_structure(self._state)
        
        if not is_valid:
            logger.warning(f"State validation errors: {errors}")
            # Merge with default to fix missing keys
            self._state = merge_dicts(DEFAULT_STATE.copy(), self._state)
        
        # Check version and migrate
        current_version = self._state.get("state_version", 1)
        
        if current_version < config.STATE_VERSION:
            await self._migrate_state(current_version)
    
    async def _migrate_state(self, from_version: int) -> None:
        """Migrate state from older version."""
        logger.info(f"Migrating state from version {from_version} to {config.STATE_VERSION}")
        
        if from_version < 2:
            # Version 2 adds: concept_frequency, streak_health, evaluation_cache
            for user_id, user_data in self._state.get("users", {}).items():
                if "concept_frequency" not in user_data:
                    user_data["concept_frequency"] = {}
                if "streak_health" not in user_data:
                    user_data["streak_health"] = "safe"
                if "evaluation_count" not in user_data:
                    user_data["evaluation_count"] = 0
            
            if "evaluation_cache" not in self._state:
                self._state["evaluation_cache"] = {}
        
        self._state["state_version"] = config.STATE_VERSION
        await self.save()
    
    async def _create_state_message(self, channel: discord.TextChannel) -> None:
        """Create and pin the state message."""
        embed = self._create_state_embed()
        message = await channel.send(embed=embed)
        await message.pin()
        self._state_message_id = message.id
    
    def _create_state_embed(self) -> discord.Embed:
        """Create the state storage embed."""
        state_json = compress_for_storage(self._state)
        
        # Ensure it fits in embed (4096 char limit for description)
        if len(state_json) > 4000:
            logger.warning("State too large, truncating")
            state_json = truncate_for_embed(state_json, 4000)
        
        embed = discord.Embed(
            title="🔒 Bot State [DO NOT MODIFY]",
            description=state_json,
            color=discord.Color.dark_grey(),
            timestamp=now()
        )
        embed.set_footer(text=f"v{config.STATE_VERSION} | Last updated")
        
        return embed
    
    async def _setup_backup_thread(self, channel: discord.TextChannel) -> None:
        """Find or create backup thread."""
        try:
            # Look for existing backup thread
            threads = channel.threads
            for thread in threads:
                if thread.name == "🔐 State Backup [LOCKED]":
                    self._backup_thread_id = thread.id
                    return
            
            # Check archived threads
            async for thread in channel.archived_threads(limit=50):
                if thread.name == "🔐 State Backup [LOCKED]":
                    self._backup_thread_id = thread.id
                    # Unarchive it
                    await thread.edit(archived=False)
                    return
            
            # Create new backup thread
            thread = await channel.create_thread(
                name="🔐 State Backup [LOCKED]",
                type=discord.ChannelType.public_thread,
                auto_archive_duration=10080  # 7 days
            )
            self._backup_thread_id = thread.id
            
            # Send initial message
            await thread.send(
                embed=discord.Embed(
                    title="State Backup Thread",
                    description="This thread stores backup copies of bot state.\n"
                               "**DO NOT DELETE OR MODIFY MESSAGES IN THIS THREAD.**",
                    color=discord.Color.red()
                )
            )
            
            logger.info(f"Created backup thread {thread.id}")
            
        except Exception as e:
            logger.error(f"Failed to setup backup thread: {e}")
    
    async def save(self, create_backup: bool = False) -> bool:
        """
        Save current state to Discord.
        
        Args:
            create_backup: Whether to also save to backup thread
        """
        async with self._lock:
            try:
                if not self._state_message_id:
                    logger.error("No state message ID")
                    return False
                
                channel = self.bot.get_channel(config.STATE_CHANNEL_ID)
                if not channel:
                    channel = await self.bot.fetch_channel(config.STATE_CHANNEL_ID)
                
                message = await channel.fetch_message(self._state_message_id)
                
                # Update state metadata
                self._state["last_updated"] = format_datetime(now())
                
                # Create new embed
                embed = self._create_state_embed()
                await message.edit(embed=embed)
                
                self._last_save = now()
                
                # Create backup if requested
                if create_backup and self._backup_thread_id:
                    await self._save_backup()
                
                logger.debug("State saved successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
                return False
    
    async def _save_backup(self) -> None:
        """Save a backup copy to the backup thread."""
        try:
            thread = self.bot.get_channel(self._backup_thread_id)
            if not thread:
                thread = await self.bot.fetch_channel(self._backup_thread_id)
            
            if thread:
                state_json = compress_for_storage(self._state)
                
                embed = discord.Embed(
                    title=f"📦 Backup - {format_datetime(now())}",
                    description=truncate_for_embed(state_json, 4000),
                    color=discord.Color.blue(),
                    timestamp=now()
                )
                
                await thread.send(embed=embed)
                logger.info("Backup saved to thread")
                
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
    
    async def force_backup(self) -> bool:
        """Force create a backup."""
        return await self.save(create_backup=True)
    
    # User State Methods
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user data."""
        return self._state.get("users", {}).get(str(user_id))
    
    async def update_user(self, user_id: int, updates: dict) -> bool:
        """Update user data."""
        user_key = str(user_id)
        
        if user_key not in self._state.get("users", {}):
            return False
        
        self._state["users"][user_key].update(updates)
        return await self.save()
    
    async def add_points(self, user_id: int, points: int) -> int:
        """Add points to user and return new total."""
        user = self.get_user(user_id)
        if not user:
            return 0
        
        new_total = user.get("points", 0) + points
        await self.update_user(user_id, {"points": new_total})
        return new_total
    
    async def update_streak(
        self,
        user_id: int,
        log_date: str,
        increment: bool = True
    ) -> tuple[int, str]:
        """
        Update user streak based on log date.
        
        Returns:
            Tuple of (new_streak, streak_health)
        """
        user = self.get_user(user_id)
        if not user:
            return 0, "broken"
        
        last_log = user.get("last_log_date")
        current_streak = user.get("streak", 0)
        
        from utils import is_consecutive_day, is_same_day, yesterday
        
        if not last_log:
            # First log ever
            new_streak = 1 if increment else 0
            health = "safe"
        elif is_same_day(last_log, log_date):
            # Already logged today
            new_streak = current_streak
            health = "safe"
        elif is_consecutive_day(last_log, log_date):
            # Consecutive day
            new_streak = current_streak + 1 if increment else current_streak
            health = "safe"
        elif last_log == yesterday():
            # Yesterday, maintaining streak
            new_streak = current_streak + 1 if increment else current_streak
            health = "safe"
        else:
            # Streak broken
            new_streak = 1 if increment else 0
            health = "broken"
        
        max_streak = max(user.get("max_streak", 0), new_streak)
        
        await self.update_user(user_id, {
            "streak": new_streak,
            "max_streak": max_streak,
            "last_log_date": log_date,
            "streak_health": health,
        })
        
        return new_streak, health
    
    async def update_concept_frequency(
        self,
        user_id: int,
        concepts: list[str]
    ) -> dict[str, int]:
        """Update user's concept frequency map."""
        user = self.get_user(user_id)
        if not user:
            return {}
        
        freq = user.get("concept_frequency", {}).copy()
        for concept in concepts:
            freq[concept] = freq.get(concept, 0) + 1
        
        await self.update_user(user_id, {"concept_frequency": freq})
        return freq
    
    async def increment_total_logs(self, user_id: int) -> int:
        """Increment total logs and return new count."""
        user = self.get_user(user_id)
        if not user:
            return 0
        
        new_total = user.get("total_logs", 0) + 1
        days_active = user.get("days_active", 0)
        
        # Check if this is first log of day
        last_log = user.get("last_log_date")
        from utils import today
        if last_log != today():
            days_active += 1
        
        await self.update_user(user_id, {
            "total_logs": new_total,
            "days_active": days_active,
        })
        
        return new_total
    
    async def award_badge(self, user_id: int, badge_id: str) -> bool:
        """Award a badge to user."""
        user = self.get_user(user_id)
        if not user:
            return False
        
        badges = user.get("badges", [])
        if badge_id not in badges:
            badges.append(badge_id)
            await self.update_user(user_id, {"badges": badges})
            return True
        return False
    
    async def update_skill_level(self, user_id: int) -> tuple[int, bool]:
        """
        Update user's skill level based on points.
        
        Returns:
            Tuple of (new_level, level_changed)
        """
        user = self.get_user(user_id)
        if not user:
            return 0, False
        
        points = user.get("points", 0)
        current_level = user.get("skill_level", 0)
        
        # Find appropriate level
        new_level = 0
        for level, data in config.SKILL_LEVELS.items():
            if points >= data["min_points"]:
                new_level = level
        
        if new_level != current_level:
            await self.update_user(user_id, {"skill_level": new_level})
            return new_level, True
        
        return current_level, False
    
    # Daily Flags
    
    async def set_daily_flag(
        self,
        user_id: int,
        flag_name: str,
        value: Any = True
    ) -> None:
        """Set a daily flag for user."""
        date_key = today()
        
        if "daily_flags" not in self._state:
            self._state["daily_flags"] = {}
        
        if date_key not in self._state["daily_flags"]:
            self._state["daily_flags"][date_key] = {}
        
        user_key = str(user_id)
        if user_key not in self._state["daily_flags"][date_key]:
            self._state["daily_flags"][date_key][user_key] = {}
        
        self._state["daily_flags"][date_key][user_key][flag_name] = value
        await self.save()
    
    def get_daily_flag(
        self,
        user_id: int,
        flag_name: str,
        default: Any = None
    ) -> Any:
        """Get a daily flag for user."""
        from utils import today
        date_key = today()
        
        return safe_get(
            self._state,
            "daily_flags", date_key, str(user_id), flag_name,
            default=default
        )
    
    def has_evaluated_today(self, user_id: int) -> bool:
        """Check if user has been evaluated today."""
        return self.get_daily_flag(user_id, "evaluated", False)
    
    async def mark_evaluated(self, user_id: int) -> None:
        """Mark user as evaluated for today."""
        await self.set_daily_flag(user_id, "evaluated", True)
        
        # Update user evaluation count
        user = self.get_user(user_id)
        if user:
            count = user.get("evaluation_count", 0) + 1
            await self.update_user(user_id, {"evaluation_count": count})
        
        # Update bot metadata
        self._state["bot_metadata"]["total_evaluations"] = \
            self._state["bot_metadata"].get("total_evaluations", 0) + 1
    
    # Evaluation Cache
    
    async def cache_evaluation(
        self,
        user_id: int,
        date: str,
        evaluation: dict
    ) -> None:
        """Cache evaluation result."""
        if "evaluation_cache" not in self._state:
            self._state["evaluation_cache"] = {}
        
        user_key = str(user_id)
        if user_key not in self._state["evaluation_cache"]:
            self._state["evaluation_cache"][user_key] = {}
        
        # Keep only last 7 evaluations
        cache = self._state["evaluation_cache"][user_key]
        if len(cache) >= 7:
            oldest = min(cache.keys())
            del cache[oldest]
        
        cache[date] = evaluation
        
        # Also update user's last evaluation
        await self.update_user(user_id, {"last_evaluation": evaluation})
        await self.save()
    
    def get_cached_evaluations(
        self,
        user_id: int,
        days: int = 7
    ) -> dict[str, dict]:
        """Get cached evaluations for user."""
        cache = safe_get(
            self._state,
            "evaluation_cache", str(user_id),
            default={}
        )
        
        from utils import get_last_n_days
        recent_dates = get_last_n_days(days)
        
        return {
            date: cache[date]
            for date in recent_dates
            if date in cache
        }
    
    # Thread Management
    
    async def set_daily_thread(
        self,
        user_id: int,
        thread_id: int
    ) -> None:
        """Set user's current daily thread ID."""
        await self.update_user(user_id, {"daily_thread_id": thread_id})
    
    def get_daily_thread(self, user_id: int) -> Optional[int]:
        """Get user's current daily thread ID."""
        user = self.get_user(user_id)
        return user.get("daily_thread_id") if user else None
    
    # Cleanup
    
    async def cleanup_old_flags(self, keep_days: int = 7) -> None:
        """Remove old daily flags to save space."""
        from utils import get_last_n_days
        
        recent_dates = set(get_last_n_days(keep_days))
        
        if "daily_flags" in self._state:
            old_dates = [
                date for date in self._state["daily_flags"]
                if date not in recent_dates
            ]
            
            for date in old_dates:
                del self._state["daily_flags"][date]
            
            if old_dates:
                await self.save()
                logger.info(f"Cleaned up {len(old_dates)} old daily flags")
    
    # Health Check
    
    def get_health_status(self) -> dict:
        """Get state manager health status."""
        return {
            "initialized": self._initialized,
            "state_message_id": self._state_message_id,
            "backup_thread_id": self._backup_thread_id,
            "last_save": format_datetime(self._last_save) if self._last_save else None,
            "state_version": self._state.get("state_version"),
            "user_count": len(self._state.get("users", {})),
            "state_size_bytes": len(compress_for_storage(self._state)),
        }
    
    def get_all_users(self) -> list[dict]:
        """Get all user data."""
        return list(self._state.get("users", {}).values())
    
    async def reset_daily_state(self) -> None:
        """Reset daily-specific state (called at day boundary)."""
        # Update streak health for all users
        from utils import today, is_consecutive_day
        
        for user_id, user_data in self._state.get("users", {}).items():
            last_log = user_data.get("last_log_date")
            
            if last_log and not is_consecutive_day(last_log, today()):
                # User hasn't logged yet today
                if user_data.get("streak_health") == "safe":
                    await self.update_user(int(user_id), {"streak_health": "at-risk"})
        
        await self.save()
