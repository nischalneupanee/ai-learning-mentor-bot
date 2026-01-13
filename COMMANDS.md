# 🤖 AI Learning Mentor Bot - Command Reference

## 📋 Quick Setup Commands

### **Initial Bot Setup**
1. `/admin setup_channels` - Auto-create all required channels
2. `/admin initialize_users` - Initialize tracking for configured users
3. `/help` - Show this command list

---

## 👤 User Commands

### **Learning & Progress**
- `/mystatus` - Get AI-generated comprehensive status report with insights and recommendations
- `/ask <question>` - Ask the AI mentor anything about your learning journey
- `/stats` - View your personal learning statistics
- `/streak` - Check your current streak status and history
- `/progress` - View your career pathway progress with milestone breakdown
- `/goals` - View and manage your learning goals
- `/todayplan` - Get AI-generated daily study plan based on your progress

### **Insights & Analytics**
- `/insights` - Get detailed AI analysis of your learning patterns
- `/concepts` - View all concepts you've learned with mastery levels
- `/weaknesses` - Identify areas that need more focus
- `/strengths` - See what you're excelling at
- `/compare <user>` - Compare your progress with another learner
- `/leaderboard` - View the global leaderboard

### **Productivity**
- `/reminder <time> <message>` - Set a learning reminder
- `/focus <duration>` - Start a focus timer (Pomodoro style)
- `/break` - Take a scheduled break with timer

---

## 🛡️ Admin Commands
*(Requires Administrator permission)*

### **Setup & Configuration**
- `/admin setup_channels` - Create all required channels automatically
- `/admin initialize_users` - Initialize user tracking
- `/admin set_goal <user> <goal>` - Set learning goal for a user
- `/admin add_user <user>` - Add a new user to tracking

### **State Management**
- `/admin health` - Check bot health and system status
- `/admin backup_state` - Create manual backup of all data
- `/admin restore_state` - Restore from backup
- `/admin reset_day` - Reset daily flags for all users
- `/admin export_data` - Export all data as JSON

### **User Management**
- `/admin recalculate_stats <user>` - Recalculate user stats from history
- `/admin force_evaluate <user>` - Force evaluation for a user
- `/admin adjust_points <user> <points>` - Manually adjust user points
- `/admin reset_streak <user>` - Reset user's streak
- `/admin set_level <user> <level>` - Set user's skill level

### **Testing & Simulation**
- `/admin simulate_day <user> <logs>` - Simulate a day with test logs
- `/admin test_notification` - Test notification system
- `/admin clear_cache` - Clear evaluation cache
- `/admin refresh_dashboard` - Manually refresh dashboard

---

## 🎯 How to Use Each Command

### For Users:

**Getting Started:**
```
/mystatus - See where you are in your learning journey
/progress - View your career pathway and next milestone
/todayplan - Get today's recommended study plan
```

**Daily Learning:**
```
1. Post your learning logs in #📚-learning-logs or your daily thread
2. Bot automatically tracks points, streak, and concepts
3. Use /ask to get help from AI mentor anytime
4. Check /stats to see your progress
```

**Weekly Review:**
```
/insights - Deep analysis of your week
/strengths - What you're doing well
/weaknesses - What needs attention
/goals - Update your goals based on progress
```

### For Admins:

**Initial Setup (Do this first!):**
```
1. /admin setup_channels - Creates all needed channels
2. Configure USER_IDS in .env file
3. /admin initialize_users - Sets up user tracking
4. /admin health - Verify everything is working
```

**Regular Maintenance:**
```
- Daily: Check /admin health
- Weekly: /admin backup_state
- Monthly: /admin export_data (for long-term backup)
```

**Troubleshooting:**
```
/admin health - Check system status
/admin recalculate_stats <user> - If stats seem wrong
/admin refresh_dashboard - If dashboard not updating
```

---

## 🔔 Automatic Features

The bot automatically:
- ✅ Tracks all learning messages with emoji reactions
- ✅ Calculates points based on depth and quality
- ✅ Maintains daily streaks
- ✅ Creates daily threads for each user
- ✅ Updates live dashboard every 5 minutes
- ✅ Sends daily evaluations with AI insights
- ✅ Sends streak reminders before deadline
- ✅ Detects and answers questions in threads
- ✅ Awards level-up notifications
- ✅ Tracks career pathway progress

---

## 📊 Point System

- **Basic log:** 10 points
- **Detailed log:** 15-25 points
- **Deep analysis:** 30-50 points
- **Streak bonus:** +5 points per day
- **Quality multiplier:** Up to 2x for exceptional work

---

## 🎓 Career Pathway Levels

**🌱 Foundation (0-500 pts)**
- Python basics, Math fundamentals, First ML models

**🌿 Intermediate (500-2000 pts)**
- Advanced algorithms, Deep learning, Model optimization

**🌳 Advanced (2000-5000 pts)**
- Research papers, Custom architectures, Production systems

**🎯 Research Expert (5000+ pts)**
- Novel research, Publications, Open-source contributions

---

## 💡 Pro Tips

1. **Daily Threads:** Use your personal daily thread for focused work and questions
2. **Ask Questions:** Don't hesitate to use `/ask` - the AI mentor is here to help!
3. **Quality over Quantity:** Deeper logs earn more points and better insights
4. **Consistency:** Daily streaks unlock multipliers and special achievements
5. **Review Insights:** Weekly `/insights` helps identify learning patterns
6. **Set Goals:** Use `/goals` to stay focused on your objectives

---

## 🆘 Troubleshooting

**Dashboard not showing?**
- Admin: `/admin refresh_dashboard`
- Check #📊-dashboard channel permissions

**No daily thread?**
- Wait up to 1 hour (auto-created hourly)
- Admin: Restart bot to force creation

**Stats seem wrong?**
- Admin: `/admin recalculate_stats <user>`
- This recalculates from full message history

**Bot not responding?**
- Admin: `/admin health` to check status
- Check Railway logs for errors

---

## 🔗 Quick Links

- **Learning Channel:** #📚-learning-logs
- **Dashboard:** #📊-dashboard  
- **Daily Threads:** #📅-daily-threads
- **Bot State:** #🤖-bot-state (admin only)

---

## 📝 Example Usage

**User wants daily plan:**
```
/todayplan
→ AI generates personalized study plan based on:
  - Current skill level
  - Recent topics
  - Career pathway stage
  - Identified weak areas
```

**User has question:**
```
/ask How do I implement attention mechanisms in transformers?
→ AI mentor provides detailed explanation with:
  - Core concepts
  - Code examples
  - Recommended resources
  - Practice exercises
```

**Admin checks health:**
```
/admin health
→ Shows:
  - Bot connection status
  - Channel availability
  - State manager health
  - Gemini API quota
```

---

*Last updated: January 2026*
*Bot Version: 2.0 - Enhanced with Career Pathways & Interactive AI Mentor*
