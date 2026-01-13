#!/usr/bin/env python3
"""
Health check script for Railway/cloud deployments.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config


def health_check() -> bool:
    """Run health checks."""
    print("Running health checks...")
    
    errors = config.validate()
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuration valid")
    print(f"✅ Guild ID: {config.GUILD_ID}")
    print(f"✅ Tracking {len(config.USER_IDS)} users")
    print(f"✅ Gemini API key configured: {'*' * 20}{config.GEMINI_API_KEY[-10:]}")
    print(f"✅ Timezone: {config.TIMEZONE}")
    
    return True


if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
