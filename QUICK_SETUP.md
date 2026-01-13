# 🚀 Quick Bot Setup Guide

## For New Installation

### Step 1: Initial Discord Setup (One-time)
1. Make sure the bot is added to your Discord server
2. Give the bot these permissions:
   - Manage Channels (to create channels)
   - Send Messages
   - Read Messages
   - Manage Threads
   - Embed Links
   - Add Reactions

### Step 2: Auto-Setup with Commands
Once your bot is running on Railway, use these commands IN ORDER:

```
1. /admin setup_channels
   → This automatically creates all 4 required channels:
      • 🤖-bot-state
      • 📚-learning-logs
      • 📊-dashboard
      • 📅-daily-threads

2. Copy the channel IDs from the bot's response
   → Update your Railway environment variables or .env file
   
3. Restart the bot (if needed)

4. /admin initialize_users
   → This sets up tracking for users in USER_IDS

5. /admin health
   → Verify everything is working correctly
```

### Step 3: Start Using!
```
/help - See all available commands
/mystatus - Check your learning status
/todayplan - Get your personalized study plan
```

---

## All Available Commands

### 👤 User Commands (Everyone can use)

#### Learning & Progress
- `/help` - Show all commands and usage
- `/mystatus` - AI-generated comprehensive status report
- `/ask <question>` - Ask the AI mentor anything
- `/stats` - View your learning statistics
- `/progress` - Career pathway progress with milestones
- `/todayplan` - Get AI daily study plan
- `/streak` - Check streak status

#### Analytics
- `/insights` - Deep AI analysis of patterns
- `/concepts` - All learned concepts
- `/leaderboard` - Global rankings

### 🛡️ Admin Commands (Requires Administrator)

#### Setup (Use these first!)
- `/admin setup_channels` - **START HERE** - Auto-create all channels
- `/admin initialize_users` - Initialize user tracking
- `/admin health` - Check system health

#### Data Management
- `/admin backup_state` - Create backup
- `/admin export_data` - Export as JSON
- `/admin recalculate_stats <user>` - Recalculate from history
- `/admin reset_day` - Reset daily flags

#### Evaluation
- `/admin force_evaluate <user>` - Force AI evaluation
- `/admin simulate_day <user> <logs>` - Test with sample data

---

## Environment Variables Needed

After running `/admin setup_channels`, update these in Railway:

```env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id

# Channel IDs (from /admin setup_channels)
STATE_CHANNEL_ID=xxxxx
LEARNING_CHANNEL_ID=xxxxx
DASHBOARD_CHANNEL_ID=xxxxx
DAILY_THREADS_CHANNEL_ID=xxxxx

# User IDs (comma-separated)
USER_IDS=user_id_1,user_id_2

# Gemini API
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-1.5-flash

# Timezone
TIMEZONE=Asia/Kathmandu
```

---

## How Students Use the Bot

### Daily Workflow:
1. **Morning**: `/todayplan` to get study plan
2. **During Study**: Post learning logs in #📚-learning-logs or your daily thread
3. **Questions**: Use `/ask <question>` anytime you're stuck
4. **Evening**: Check `/stats` to see progress

### Weekly Review:
```
/insights - See what patterns emerged this week
/progress - Check career pathway advancement
/streak - Confirm streak is maintained
```

### Anytime:
```
/concepts - Review what you've learned
/leaderboard - See how you rank
/help - Remember all commands
```

---

## What Happens Automatically

✅ Bot tracks all learning messages with reactions
✅ Calculates points based on depth/quality
✅ Maintains daily streaks
✅ Creates personal daily threads
✅ Updates dashboard every 5 minutes
✅ Sends AI evaluations daily
✅ Answers questions in threads
✅ Awards level-up notifications

---

## Example Usage Session

**Admin sets up (first time):**
```
Admin: /admin setup_channels
Bot: ✅ Created all channels! Here are the IDs...

Admin: [Updates .env, restarts]

Admin: /admin initialize_users
Bot: ✅ Initialized 2 users

Admin: /admin health
Bot: Shows all systems green ✅
```

**Student uses bot:**
```
Student: /help
Bot: Shows complete command list

Student: /mystatus
Bot: Shows current progress, career stage, recommendations

Student: /todayplan
Bot: Generates personalized 6-hour study plan

Student: [Posts in #📚-learning-logs]
"Today I learned about transformers attention mechanism.
Implemented multi-head attention from scratch..."

Bot: ✅ [Adds reactions, awards points, updates streak]

Student: /ask How does positional encoding work in transformers?
Bot: [Provides detailed AI-powered explanation]

Student: /progress
Bot: Shows career pathway progress with next milestones

Student: /leaderboard
Bot: Shows global rankings
```

---

## Troubleshooting

**Commands not showing up?**
- Bot needs time to sync (wait 1-2 minutes after deployment)
- Try typing `/` and searching for commands

**Dashboard not updating?**
- Check Railway logs for errors
- Run `/admin health` to verify channels
- Dashboard updates every 5 minutes automatically

**Daily threads not created?**
- Wait up to 1 hour (they're created hourly)
- Or restart bot to force immediate creation

**Want to test without affecting real data?**
```
/admin simulate_day @user "log 1 | log 2 | log 3"
```

---

## Pro Tips

1. **Use Daily Threads**: Each user gets a personal thread daily - great for focused work
2. **Ask Questions Often**: `/ask` is powered by Gemini - use it liberally!
3. **Check /insights Weekly**: See patterns in your learning
4. **Quality > Quantity**: Deeper logs = more points
5. **Maintain Streaks**: Daily consistency unlocks multipliers

---

## What's New in This Version

🎯 **8 New User Commands** - More ways to track and improve
📊 **Career Pathways** - Clear progression from beginner to expert
🤖 **AI Study Plans** - Personalized daily plans
🔍 **Deep Insights** - Pattern analysis of your learning
🏆 **Leaderboards** - Compete and stay motivated
⚡ **Auto Setup** - One command to create all channels
📈 **Enhanced Stats** - More detailed analytics

---

*Your AI Learning Mentor Bot is ready to help you master AI/ML! 🚀*
