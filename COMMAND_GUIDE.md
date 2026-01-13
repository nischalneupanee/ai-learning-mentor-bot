# 🤖 AI Learning Mentor Bot - Complete Command Reference

## 📋 Quick Command List

### For Everyone (User Commands)

```
📚 LEARNING & PROGRESS
/help                      → Show all commands
/mystatus                  → AI-generated status report
/ask <question>            → Ask AI mentor anything
/stats                     → Your learning statistics
/progress                  → Career pathway & milestones
/todayplan                 → AI daily study plan
/streak                    → Streak status & history

🔍 INSIGHTS & ANALYTICS
/insights                  → Deep AI pattern analysis
/concepts                  → All learned concepts
/leaderboard               → Global rankings
```

### For Admins Only

```
🚀 SETUP (Run these first!)
/admin setup_channels      → Auto-create all channels ⭐ START HERE
/admin initialize_users    → Initialize user tracking
/admin health              → System health check

💾 DATA MANAGEMENT
/admin backup_state        → Create backup
/admin export_data         → Export as JSON
/admin recalculate_stats   → Recalculate from history
/admin reset_day           → Reset daily flags

🔧 EVALUATION & TESTING
/admin force_evaluate      → Force AI evaluation
/admin simulate_day        → Test with sample logs
```

---

## 🎯 Setup Workflow (For Admins)

### First Time Setup:
```
Step 1: /admin setup_channels
        ↓
Step 2: Copy channel IDs to .env
        ↓
Step 3: Restart bot
        ↓
Step 4: /admin initialize_users
        ↓
Step 5: /admin health (verify)
        ↓
Done! ✅
```

---

## 👥 User Workflow

### Daily Learning Cycle:
```
Morning:    /todayplan        → Get study plan
            ↓
Study:      Post in #📚-learning-logs
            Use /ask for questions
            ↓
Evening:    /stats            → Check progress
            /streak           → Verify streak
```

### Weekly Review:
```
/insights   → Pattern analysis
/progress   → Career advancement
/concepts   → What you learned
/leaderboard → See rankings
```

---

## 🎨 Command Details

### `/help`
**What it does:** Shows complete command reference
**Who can use:** Everyone
**Example:**
```
/help
→ Shows categorized list of all commands
```

---

### `/mystatus`
**What it does:** AI-generated comprehensive status report
**Who can use:** Tracked users only
**Example:**
```
/mystatus
→ Current level: 🌿 Intermediate Developer
→ Points: 1,234
→ Streak: 15 days
→ AI recommendations for improvement
```

---

### `/ask <question>`
**What it does:** Ask AI mentor any question
**Who can use:** Tracked users
**Example:**
```
/ask How do I implement backpropagation?
→ Detailed AI explanation with examples
```

---

### `/stats`
**What it does:** Detailed personal statistics
**Who can use:** Tracked users
**Shows:**
- Total points & logs
- Current career stage
- Streak information
- Top concepts learned

**Example:**
```
/stats
→ 📊 Learning Stats
→ 🎯 Career: Intermediate (1,234/2,000 pts)
→ 🔥 Streak: 15 days (best: 20)
→ 🧠 Concepts: 45 learned
```

---

### `/progress`
**What it does:** Career pathway progress visualization
**Who can use:** Tracked users
**Shows:**
- Current milestone
- Progress bar to next level
- Focus areas
- Recommended topics
- Full pathway overview

**Example:**
```
/progress
→ 🌿 Intermediate Developer
→ ████████░░ 80% (1,600/2,000)
→ Focus: Deep learning, Model optimization
→ Next: 🌳 Advanced Developer
```

---

### `/todayplan`
**What it does:** AI-generated personalized study plan
**Who can use:** Tracked users
**Generates:**
- Morning session (2-3 hrs) - Deep focus
- Afternoon session (1-2 hrs) - Practice
- Evening session (1 hr) - Review
- Specific topics & resources

**Example:**
```
/todayplan
→ 📅 Today's Study Plan
→ Morning: Transformer architecture deep dive
→ Afternoon: Implement attention from scratch
→ Evening: Review and solidify concepts
→ Resources: Papers, tutorials, exercises
```

---

### `/insights`
**What it does:** AI-powered deep learning pattern analysis
**Who can use:** Tracked users (needs 5+ logs)
**Analyzes:**
- Learning patterns
- Strengths
- Areas for improvement
- Actionable recommendations
- Motivational insights

**Example:**
```
/insights
→ 🔍 Your learning shows consistency in morning hours
→ 💪 Strong: Implementation skills, persistence
→ 📈 Improve: Theoretical foundations
→ 💡 Recommendations: [5 specific suggestions]
```

---

### `/streak`
**What it does:** Current streak status and history
**Who can use:** Tracked users
**Shows:**
- Current streak
- Best streak ever
- Next milestone
- Motivational message

**Example:**
```
/streak
→ 🔥 Current: 15 days
→ 🏆 Best: 20 days
→ 🎯 Next milestone: 30 days (15 to go!)
→ 💪 You're on fire! Keep going!
```

---

### `/concepts`
**What it does:** All concepts learned with frequency
**Who can use:** Tracked users
**Shows:**
- All unique concepts
- Practice count for each
- Top concepts highlighted

**Example:**
```
/concepts
→ 🧠 Concepts Learned
→ Total: 45 unique concepts
→ 🥇 Transformers (12x)
→ 🥈 Attention (10x)
→ 🥉 Backprop (8x)
→ ▫️ CNN (7x)
```

---

### `/leaderboard`
**What it does:** Global learning rankings
**Who can use:** Everyone
**Shows:**
- Top 10 learners
- Points & career level
- Streaks & total logs

**Example:**
```
/leaderboard
→ 🏆 Learning Leaderboard
→ 🥇 John - 🌳 2,345 pts (20 day streak)
→ 🥈 Sarah - 🌿 1,890 pts (15 day streak)
→ 🥉 Mike - 🌿 1,234 pts (10 day streak)
```

---

### `/admin setup_channels` ⭐
**What it does:** Auto-creates all required channels
**Who can use:** Administrators only
**Creates:**
- 🤖-bot-state
- 📚-learning-logs
- 📊-dashboard
- 📅-daily-threads

**Example:**
```
/admin setup_channels
→ ✅ Channels Created!
→ • #🤖-bot-state (ID: 123...)
→ • #📚-learning-logs (ID: 456...)
→ • #📊-dashboard (ID: 789...)
→ • #📅-daily-threads (ID: 012...)
→ 📋 Copy these IDs to your .env file
```

---

### `/admin initialize_users`
**What it does:** Sets up tracking for configured users
**Who can use:** Administrators only
**Initializes:**
- Points to 0
- Streaks to 0
- Empty concept lists
- Message history

**Example:**
```
/admin initialize_users
→ ✅ Initialized 2 users
→ Ready to track learning!
```

---

### `/admin health`
**What it does:** Complete system health check
**Who can use:** Administrators only
**Checks:**
- State manager status
- Channel availability
- Gemini API quota
- Bot connection
- Database size

**Example:**
```
/admin health
→ 🏥 Bot Health Status
→ 📦 State: ✅ Initialized
→ 🤖 Gemini: 50 requests remaining
→ 🔌 Latency: 45ms
→ 📢 All channels: ✅
```

---

### `/admin export_data`
**What it does:** Export all bot data as JSON
**Who can use:** Administrators only
**Exports:**
- All user data
- Message history
- Statistics
- Configuration

**Example:**
```
/admin export_data
→ 📦 Here's your data export:
→ [Attaches: bot_data_export_2026-01-13.json]
```

---

## 🎓 Career Pathway Levels

Your progress through these stages:

```
🌱 Foundation (0-500 pts)
   → Python basics, Math fundamentals, First ML models

🌿 Intermediate (500-2,000 pts)
   → Advanced algorithms, Deep learning, Optimization

🌳 Advanced (2,000-5,000 pts)
   → Research papers, Custom architectures, Production

🎯 Research Expert (5,000+ pts)
   → Novel research, Publications, Contributions
```

---

## 📊 Point System

```
Basic log:          10 points
Detailed log:       15-25 points
Deep analysis:      30-50 points
Streak bonus:       +5 points/day
Quality multiplier: Up to 2x
```

---

## 💡 Pro Tips

1. **Start with /help** - Familiarize yourself with all commands
2. **Use /todayplan** - Get structured daily plans
3. **Ask Questions** - /ask is unlimited, use it!
4. **Daily Threads** - Use your personal thread for focused work
5. **Check /insights** - Weekly pattern analysis helps improve
6. **Maintain Streaks** - Consistency unlocks multipliers
7. **Quality Logs** - Deeper entries = more points

---

## 🔄 Automatic Features

The bot does these WITHOUT commands:

✅ Tracks all learning messages
✅ Awards points automatically
✅ Maintains streaks
✅ Creates daily threads
✅ Updates dashboard (every 5 min)
✅ Sends daily AI evaluations
✅ Answers questions in threads
✅ Sends streak reminders
✅ Level-up notifications

---

## 🆘 Common Issues

**Commands not showing?**
- Wait 1-2 minutes for sync
- Make sure bot has proper permissions

**Dashboard empty?**
- Check #📊-dashboard for pinned message
- Run /admin health to verify

**No daily thread?**
- Threads created hourly
- Restart bot to force creation

**Stats seem wrong?**
- /admin recalculate_stats <user>

---

## 📞 Support

Check these files for detailed help:
- `COMMANDS.md` - Full command documentation
- `QUICK_SETUP.md` - Setup guide
- `README.md` - Project overview
- Railway logs - Error details

---

**Version:** 2.0 - Enhanced Edition
**Last Updated:** January 2026
**Features:** Career Pathways, AI Mentor, Auto-Setup

🚀 Your AI Learning Mentor is ready to help you master ML/AI!
