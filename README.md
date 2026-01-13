# 🤖 AI Learning Mentor Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.5+-blue.svg)](https://github.com/Pycord-Development/pycord)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Discord bot that acts as an AI-powered learning mentor for tracking and improving your AI/ML/DL/Data Science learning journey.

**NEW in v2.0:** 8+ user commands, auto-setup, AI daily plans, career pathways, deep insights! 🚀

## ✨ What's New in Version 2.0

### 🎯 8+ New User Commands
- `/help` - Complete command reference
- `/stats` - Detailed learning statistics
- `/progress` - Career pathway visualization
- `/todayplan` - AI-generated daily study plans
- `/insights` - Deep AI pattern analysis
- `/streak` - Streak status with motivation
- `/concepts` - All learned concepts
- `/leaderboard` - Global rankings

### 🚀 Auto-Setup for Admins
- `/admin setup_channels` - One command creates ALL channels!
- `/admin initialize_users` - Initialize tracking instantly
- `/admin export_data` - Full data export
- No more manual Discord configuration

### 🎓 Career Pathway System
- 4 clear progression stages (Foundation → Research Expert)
- Visual progress bars everywhere
- Level-specific recommendations
- Milestone tracking and rewards

### 🤖 Enhanced AI Features
- Personalized daily study plans
- Deep learning pattern analysis
- Context-aware recommendations
- Smarter question answering

## 📚 Complete Feature Set

### 📊 Discord-Native Architecture
- **Zero external databases** - All state stored in Discord itself
- Pinned embed messages as primary storage
- Locked threads as backup storage
- Auto-migration between state versions

### 📈 Intelligent Tracking
- Automatic message qualification (30+ chars, no duplicates)
- Technical depth detection with keyword analysis
- Concept frequency tracking with repetition penalties
- Topic classification (AI/ML/DL/DS)

### 🔥 Streak System
- Timezone-aware streak tracking
- Grace period until 3 AM
- Streak health indicators (safe/at-risk/broken)
- Smart, non-spam reminders
- Milestone celebrations (7, 14, 30, 50, 100 days)

### 🎮 Gamification & Career Progression
- **Points system** with base + depth bonuses
- **Career Pathway**: Foundation → Intermediate → Advanced → Research Expert
- **Skill levels** with clear milestones
- **Visual progress bars** in all commands
- **Competitive leaderboard** with rankings

### 🧠 AI-Powered Insights
- Daily evaluations with Google Gemini
- Personalized study plan generation
- Deep pattern analysis of learning habits
- Confidence-weighted feedback
- Weekly AI mentor summaries
- Context-aware question answering

### 💬 Interactive Features
- Personal daily threads for each learner
- AI mentor Q&A in threads (`/ask` command)
- Auto-detection of questions
- Real-time dashboard updates
- Motivational notifications

## 🚀 Quick Start

### Cloud Deployment (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click the button above or go to [Railway](https://railway.app)
2. Sign in with GitHub and select this repository
3. Add environment variables (see `.env.example`)
4. Deploy! ✨
5. **In Discord, run:** `/admin setup_channels` to auto-create all channels
6. Update Railway env vars with channel IDs
7. Restart bot and run `/admin initialize_users`
8. Done! Use `/help` to see all commands

**📖 Detailed Setup:** See [QUICK_SETUP.md](QUICK_SETUP.md)

### Local Development

**Prerequisites:**
- Python 3.11+
- Discord Bot with Administrator permissions
- Google Gemini API key (free tier)

**Installation:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/nischalneupanee/ai-learning-mentor-bot.git
   cd ai-learning-mentor-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Create Discord channels**
   Create these channels in your Discord server:
   - `#bot-state` (private, only bot can see)
   - `#learning-logs` (where users post)
   - `#dashboard` (for stats display)
   - `#daily-threads` (for auto-created threads)

6. **Run the bot**
   ```bash
   python bot.py
   ```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Your Discord bot token |
| `GUILD_ID` | Your Discord server ID |
| `STATE_CHANNEL_ID` | Private channel for state storage |
| `LEARNING_CHANNEL_ID` | Channel for learning logs |
| `DASHBOARD_CHANNEL_ID` | Channel for dashboard |
| `DAILY_THREADS_CHANNEL_ID` | Channel for daily threads |
| `USER_IDS` | Comma-separated user IDs (exactly 2) |
| `GEMINI_API_KEY` | Google Gemini API key |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `TIMEZONE` | `Asia/Kathmandu` | Timezone for streak calculations |

## 📝 Slash Commands

### 👤 User Commands

| Command | Description |
|---------|-------------|
| `/help` | Complete command reference with examples |
| `/mystatus` | AI-generated comprehensive status report |
| `/ask <question>` | Ask AI mentor anything |
| `/stats` | View detailed learning statistics |
| `/progress` | Career pathway progress with milestones |
| `/todayplan` | AI-generated personalized daily study plan |
| `/insights` | Deep AI analysis of learning patterns |
| `/streak` | Streak status with motivation |
| `/concepts` | All learned concepts with frequency |
| `/leaderboard` | Global rankings with levels |

### 🛡️ Admin Commands

#### Setup & Management
| Command | Description |
|---------|-------------|
| `/admin setup_channels` | ⭐ Auto-create all required channels |
| `/admin initialize_users` | Initialize user tracking |
| `/admin health` | Complete system health check |
| `/admin backup_state` | Create state backup |
| `/admin export_data` | Export all data as JSON |

#### User Management
| Command | Description |
|---------|-------------|
| `/admin recalculate_stats` | Recalculate user stats from history |
| `/admin force_evaluate` | Force run AI evaluation |
| `/admin reset_day` | Reset daily flags |
| `/admin set_points` | Manually adjust user points |
| `/admin set_streak` | Manually set user streak |

#### Testing
| Command | Description |
|---------|-------------|
| `/admin simulate_day` | Test evaluation with custom logs |

**📖 Full Command Documentation:** See [COMMANDS.md](COMMANDS.md) and [COMMAND_GUIDE.md](COMMAND_GUIDE.md)

## 📦 State Structure

The bot stores all state in a pinned embed's description as compressed JSON:

```json
{
  "state_version": 2,
  "last_updated": "2024-01-15 14:30:00",
  "bot_metadata": {
    "version": "1.0.0",
    "started_at": "2024-01-01 00:00:00",
    "total_evaluations": 42
  },
  "users": {
    "123456789": {
      "user_id": 123456789,
      "username": "learner1",
      "points": 1500,
      "streak": 14,
      "max_streak": 30,
      "skill_level": 1,
      "badges": ["first_log", "streak_7"],
      "concept_frequency": {
        "neural network": 5,
        "gradient descent": 3
      },
      "topic_coverage": {
        "AI": 10,
        "ML": 15,
        "DL": 8,
        "DS": 5
      }
    }
  },
  "daily_flags": {},
  "evaluation_cache": {}
}
```

## 🎖️ Badges

| Badge | Requirement |
|-------|-------------|
| 👶 First Steps | Log first learning entry |
| 🔥 Week Warrior | 7-day streak |
| 💎 Month Master | 30-day streak |
| 👑 Century Scholar | 100-day streak |
| 🧠 Deep Diver | Achieve depth score 9+ |
| 🌟 Renaissance Mind | Cover all 4 domains |
| ⚡ Consistency King | 10 consecutive high-quality days |

## 🏆 Career Pathway Levels

| Level | Name | Points Required | Focus Areas |
|-------|------|----------------|-------------|
| 0 | 🌱 Foundation | 0-500 | Python basics, Math fundamentals, First ML models |
| 1 | 🌿 Intermediate | 500-2,000 | Advanced algorithms, Deep learning, Optimization |
| 2 | 🌳 Advanced | 2,000-5,000 | Research papers, Custom architectures, Production |
| 3 | 🎯 Research Expert | 5,000+ | Novel research, Publications, Contributions |

Each level provides:
- Specific learning recommendations
- Milestone celebrations
- Visual progress tracking
- AI-personalized study plans

## 🔒 Permissions Checklist

The bot requires these Discord permissions:
- ✅ Read Messages/View Channels
- ✅ Send Messages
- ✅ Manage Messages (for pins)
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Use Slash Commands
- ✅ Create Public Threads
- ✅ Send Messages in Threads
- ✅ Manage Threads
- ✅ **Manage Channels** (for `/admin setup_channels`)

**Easy Setup:** Use `/admin setup_channels` to auto-create all channels with proper settings!

## 📖 Documentation

- **[QUICK_SETUP.md](QUICK_SETUP.md)** - Step-by-step setup guide
- **[COMMANDS.md](COMMANDS.md)** - Complete command reference with examples
- **[COMMAND_GUIDE.md](COMMAND_GUIDE.md)** - Detailed command explanations
- **[CHEAT_SHEET.md](CHEAT_SHEET.md)** - Quick reference card
- **[WHATS_NEW.md](WHATS_NEW.md)** - Version 2.0 features and improvements

## 🖥️ Running as a Service

### Using systemd (Linux)

1. **Copy the service file**
   ```bash
   sudo cp learning-mentor-bot.service /etc/systemd/system/
   ```

2. **Edit the service file**
   ```bash
   sudo nano /etc/systemd/system/learning-mentor-bot.service
   # Update User, Group, WorkingDirectory, and ExecStart paths
   ```

3. **Enable and start**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable learning-mentor-bot
   sudo systemctl start learning-mentor-bot
   ```

4. **Check status**
   ```bash
   sudo systemctl status learning-mentor-bot
   sudo journalctl -u learning-mentor-bot -f  # Follow logs
   ```

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

## 📄 License

MIT License - Feel free to use and modify.

---

Made with ❤️ for AI/ML learners
