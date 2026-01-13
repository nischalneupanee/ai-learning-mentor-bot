"""
Timezone utilities for the AI Learning Mentor Bot.
Handles all date/time operations with proper timezone awareness.
"""

from datetime import datetime, timedelta, time
from typing import Optional
import pytz
from config import config


def get_timezone() -> pytz.timezone:
    """Get the configured timezone object."""
    return pytz.timezone(config.TIMEZONE)


def now() -> datetime:
    """Get current datetime in configured timezone."""
    return datetime.now(get_timezone())


def today() -> str:
    """Get today's date string in YYYY-MM-DD format."""
    return now().strftime("%Y-%m-%d")


def yesterday() -> str:
    """Get yesterday's date string in YYYY-MM-DD format."""
    return (now() - timedelta(days=1)).strftime("%Y-%m-%d")


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string to datetime object."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return get_timezone().localize(dt)
    except ValueError:
        return None


def format_date(dt: datetime) -> str:
    """Format datetime to date string."""
    return dt.strftime("%Y-%m-%d")


def format_datetime(dt: datetime) -> str:
    """Format datetime to full string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_effective_date() -> str:
    """
    Get the effective date for logging purposes.
    Accounts for grace period (logs before 3 AM count as previous day).
    """
    current = now()
    grace_time = time(hour=config.STREAK_GRACE_HOUR, minute=0)
    
    if current.time() < grace_time:
        return (current - timedelta(days=1)).strftime("%Y-%m-%d")
    return current.strftime("%Y-%m-%d")


def is_within_grace_period() -> bool:
    """Check if current time is within the grace period."""
    current = now()
    grace_time = time(hour=config.STREAK_GRACE_HOUR, minute=0)
    return current.time() < grace_time


def get_streak_deadline() -> datetime:
    """Get the deadline for maintaining today's streak."""
    current = now()
    if is_within_grace_period():
        # Deadline is 3 AM today
        deadline = current.replace(
            hour=config.STREAK_GRACE_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
    else:
        # Deadline is 3 AM tomorrow
        tomorrow = current + timedelta(days=1)
        deadline = tomorrow.replace(
            hour=config.STREAK_GRACE_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
    return deadline


def time_until_deadline() -> timedelta:
    """Get time remaining until streak deadline."""
    return get_streak_deadline() - now()


def format_time_remaining(td: timedelta) -> str:
    """Format timedelta to human-readable string."""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "Expired"
    
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def days_between(date1: str, date2: str) -> int:
    """Calculate days between two date strings."""
    d1 = parse_date(date1)
    d2 = parse_date(date2)
    
    if not d1 or not d2:
        return -1
    
    return abs((d2 - d1).days)


def is_consecutive_day(last_date: str, current_date: str) -> bool:
    """Check if current_date is exactly one day after last_date."""
    return days_between(last_date, current_date) == 1


def is_same_day(date1: str, date2: str) -> bool:
    """Check if two date strings represent the same day."""
    return date1 == date2


def get_week_start(date_str: Optional[str] = None) -> str:
    """Get the Monday of the week for given date."""
    if date_str:
        dt = parse_date(date_str)
        if not dt:
            dt = now()
    else:
        dt = now()
    
    # Monday = 0, Sunday = 6
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    return monday.strftime("%Y-%m-%d")


def get_week_dates(week_start: Optional[str] = None) -> list[str]:
    """Get list of date strings for the week."""
    if week_start:
        start = parse_date(week_start)
        if not start:
            start = parse_date(get_week_start())
    else:
        start = parse_date(get_week_start())
    
    if not start:
        return []
    
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def get_last_n_days(n: int) -> list[str]:
    """Get list of last N date strings including today."""
    current = now()
    return [(current - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]


def get_daily_thread_name() -> str:
    """Get the thread name for today's daily thread."""
    current = now()
    return current.strftime("📚 %B %d, %Y")


def get_readable_date(date_str: str) -> str:
    """Convert date string to readable format."""
    dt = parse_date(date_str)
    if not dt:
        return date_str
    return dt.strftime("%B %d, %Y")


def get_streak_status_emoji(streak: int) -> str:
    """Get emoji based on streak length."""
    if streak >= 100:
        return "👑"
    elif streak >= 30:
        return "💎"
    elif streak >= 7:
        return "🔥"
    elif streak >= 3:
        return "⭐"
    elif streak >= 1:
        return "✨"
    return "💤"


def should_send_reminder(last_log_date: Optional[str]) -> tuple[bool, str]:
    """
    Determine if a streak reminder should be sent.
    Returns (should_send, reason).
    """
    if not last_log_date:
        return False, ""
    
    effective = get_effective_date()
    
    # Already logged today
    if last_log_date == effective:
        return False, ""
    
    current = now()
    hour = current.hour
    
    # Evening reminder (after 8 PM, before midnight)
    if 20 <= hour < 24:
        remaining = time_until_deadline()
        hours_left = remaining.total_seconds() / 3600
        
        if hours_left <= 7:  # Less than 7 hours
            return True, f"⚠️ Streak at risk! {format_time_remaining(remaining)} until deadline!"
    
    # Early morning reminder (during grace period)
    if is_within_grace_period():
        remaining = time_until_deadline()
        hours_left = remaining.total_seconds() / 3600
        
        if hours_left <= 2:  # Less than 2 hours in grace period
            return True, f"🚨 URGENT: Only {format_time_remaining(remaining)} left to save your streak!"
    
    return False, ""
