# 🤖 AI Learning Mentor Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.5+-blue.svg)](https://github.com/Pycord-Development/pycord)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Discord bot that acts as an AI-powered learning mentor for tracking and improving your AI/ML/DL/Data Science learning journey.

## ✨ Features

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

### 🎮 Gamification
- **Points system** with base + depth bonuses
- **Skill levels**: Beginner → Intermediate → Advanced → Researcher
- **Badges** for milestones and achievements
- **Competitive leaderboard**

### 🧠 AI-Powered Insights
- Daily evaluations with Google Gemini
- Split Analyzer + Mentor prompts
- Confidence-weighted feedback
- Weekly AI mentor summaries
- Personalized goal trajectories

## 🚀 Quick Start

### Cloud Deployment (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click the button above or go to [Railway](https://railway.app)
2. Sign in with GitHub and select this repository
3. Add environment variables (see `.env.example`)
4. Deploy! ✨

### Local Development

**Prerequisites:**
- Python 3.11+
- Discord Bot with Administrator permissions
- Google Gemini API key (free tier)

**Installation:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-learning-mentor-bot.git
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

### User Commands
| Command | Description |
|---------|-------------|
| `/stats` | View personal statistics |
| `/streak` | Check streak status and health |
| `/leaderboard` | View competitive rankings |
| `/goal` | Get AI-generated learning trajectory |
| `/summary` | Weekly AI mentor report |
| `/badges` | View badge collection |
| `/export` | Export logs as text file |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/admin health` | Check bot health status |
| `/admin reset_day` | Reset daily flags |
| `/admin recalculate_stats` | Recalculate user stats |
| `/admin force_evaluate` | Force run evaluation |
| `/admin backup_state` | Create state backup |
| `/admin simulate_day` | Test evaluation with custom logs |
| `/admin set_role` | Set user skill level |
| `/admin view_state` | View raw state JSON |
| `/admin cleanup` | Clean old daily flags |
| `/admin award_badge` | Manually award badge |
| `/admin set_points` | Set user points |
| `/admin set_streak` | Set user streak |

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

## 🏆 Skill Levels

| Level | Name | Required Points |
|-------|------|-----------------|
| 0 | 🌱 Beginner | 0 |
| 1 | 📚 Intermediate | 500 |
| 2 | 🚀 Advanced | 2000 |
| 3 | 🎓 Researcher | 5000 |

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
- ✅ Manage Roles (for skill level roles)

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
