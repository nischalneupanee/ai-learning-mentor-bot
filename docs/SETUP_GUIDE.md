# Setup Guide - AI Learning Mentor Bot

A complete step-by-step guide to deploy your AI Learning Mentor Bot.

---

## 📋 Prerequisites

Before starting, ensure you have:

| Requirement | Details |
|-------------|---------|
| **Python** | Version 3.11 or higher ([Download](https://python.org/downloads)) |
| **Discord Account** | With a server you own/admin |
| **Google Account** | For Gemini API (free tier) |
| **Text Editor** | VS Code, nano, or similar |
| **Terminal Access** | Command line basics |

---

## Step 1: Create a Discord Bot

### 1.1 Create a New Application

1. Open [Discord Developer Portal](https://discord.com/developers/applications)
2. Sign in with your Discord account
3. Click the **"New Application"** button (top right)
4. Enter a name: `AI Learning Mentor`
5. Accept the Developer Terms of Service
6. Click **"Create"**

> 💡 **Tip:** The application name will be your bot's default username.

### 1.2 Configure the Bot

1. In the left sidebar, click **"Bot"**
2. Your bot is automatically created with the application

#### Get Your Bot Token
1. Under the **Token** section, click **"Reset Token"**
2. Click **"Yes, do it!"** to confirm
3. Click **"Copy"** to copy your token

> ⚠️ **IMPORTANT:** Store this token securely! Never share it or commit it to git. Anyone with this token can control your bot.

#### Enable Privileged Intents
Scroll down to **Privileged Gateway Intents** and enable:

| Intent | Why Needed |
|--------|------------|
| ✅ **Server Members Intent** | Track specific users |
| ✅ **Message Content Intent** | Read learning log messages |

Click **"Save Changes"** at the bottom.

#### Optional: Customize Bot Profile
- Click on the bot's avatar to upload a custom image
- Add a description in the "About Me" section

### 1.3 Generate Invite URL

1. In the left sidebar, click **"Installation"**
2. Under **Installation Contexts**, ensure **"Guild Install"** is checked
3. Under **Default Install Settings** → **Guild Install**:
   - Set **Scopes**: `bot`, `applications.commands`
   - Set **Permissions**: `Administrator` (or select individual permissions below)

   <details>
   <summary>📜 Click for individual permissions list</summary>

   If you prefer not to use Administrator:
   - Read Messages/View Channels
   - Send Messages
   - Send Messages in Threads
   - Create Public Threads
   - Manage Messages
   - Manage Threads
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Use Slash Commands
   - Manage Roles

   </details>

4. Copy the **Install Link** at the top of the page
5. Open the link in your browser
6. Select your server from the dropdown
7. Click **"Continue"** → **"Authorize"**
8. Complete the CAPTCHA if prompted

✅ Your bot should now appear in your server (offline until you run it).

---

## Step 2: Get Gemini API Key (Free)

Google Gemini offers a generous free tier perfect for this bot.

### 2.1 Access Google AI Studio

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Accept the terms of service if prompted

### 2.2 Create an API Key

1. Click **"Get API Key"** in the left sidebar (or top navigation)
2. Click **"Create API Key"**
3. Select **"Create API key in new project"** (or choose an existing project)
4. Your API key will be generated and displayed
5. Click the **copy icon** to copy the key

> ⚠️ **IMPORTANT:** Store this key securely! Don't share it publicly.

### 2.3 Free Tier Limits (as of 2026)

| Model | Rate Limit | Daily Limit |
|-------|------------|-------------|
| `gemini-1.5-flash` | 15 RPM | 1,500 requests/day |
| `gemini-1.5-pro` | 2 RPM | 50 requests/day |

The bot uses `gemini-1.5-flash` by default, which is plenty for 2 users.

---

## Step 3: Prepare Your Discord Server

### 3.1 Enable Developer Mode

First, enable Developer Mode to copy IDs:

1. Open Discord Settings (⚙️ gear icon)
2. Go to **App Settings** → **Advanced**
3. Toggle **Developer Mode** → ON

### 3.2 Create Required Channels

Create these 4 channels in your server:

| Channel | Type | Setup | Purpose |
|---------|------|-------|---------|
| `#🔒-bot-state` | Text | Private (bot only sees) | Stores bot data |
| `#📚-learning-logs` | Text | Public | Users post learning here |
| `#📊-dashboard` | Text | Read-only for users | Live stats display |
| `#📅-daily-threads` | Text | Public | Auto-created daily threads |

#### How to Make `#🔒-bot-state` Private:
1. Right-click the channel → **Edit Channel**
2. Go to **Permissions**
3. Click **@everyone** → Deny **"View Channel"**
4. Click **Add members or roles** → Select your bot
5. Allow **"View Channel"**, **"Send Messages"**, **"Manage Messages"**
6. Save Changes

### 3.3 Copy Required IDs

You need to copy these IDs:

#### Server (Guild) ID
1. Right-click your **server icon** (left sidebar)
2. Click **"Copy Server ID"**
3. Save this as `GUILD_ID`

#### Channel IDs
For each channel you created:
1. Right-click the channel name
2. Click **"Copy Channel ID"**
3. Save each ID with its corresponding name

#### User IDs
For each user to track (exactly 2):
1. Right-click the user's name/avatar
2. Click **"Copy User ID"**
3. Save both IDs

### 3.4 Create Skill Level Roles (Optional)

These roles are auto-assigned as users level up:

| Role Name | Color Suggestion |
|-----------|------------------|
| 🌱 Beginner | Green |
| 📚 Intermediate | Blue |
| 🚀 Advanced | Purple |
| 🎓 Researcher | Gold |

**To create roles:**
1. Server Settings → **Roles**
2. Click **"Create Role"**
3. Name it exactly as shown above
4. Drag the roles so the bot's role is **above** these roles

---

## Step 4: Install the Bot

### 4.1 Download/Clone the Bot Files

Ensure you have all bot files in a folder (e.g., `~/study-bot/`).

### 4.2 Set Up Python Environment

Open your terminal and run:

```bash
# Navigate to the bot folder
cd ~/study-bot

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate   # Linux/Mac
# OR
.\venv\Scripts\activate    # Windows PowerShell
```

> 💡 Your terminal prompt should now show `(venv)` indicating the virtual environment is active.

### 4.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Expected output:
```
Successfully installed py-cord aiohttp python-dotenv pytz ...
```

### 4.4 Configure Environment Variables

```bash
# Create your config file from the template
cp .env.example .env

# Edit the file
nano .env   # or: code .env (VS Code) / notepad .env (Windows)
```

Fill in your `.env` file with the IDs you collected:

```env
# Discord Bot Token (from Step 1.2)
DISCORD_TOKEN=your_bot_token_here

# Server ID (from Step 3.3)
GUILD_ID=your_guild_id_here

# Channel IDs (from Step 3.3)
STATE_CHANNEL_ID=your_state_channel_id
LEARNING_CHANNEL_ID=your_learning_channel_id
DASHBOARD_CHANNEL_ID=your_dashboard_channel_id
DAILY_THREADS_CHANNEL_ID=your_threads_channel_id

# User IDs - comma separated, exactly 2 users
USER_IDS=user_id_1,user_id_2

# Gemini API Key (from Step 2.2)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional settings
GEMINI_MODEL=gemini-1.5-flash
TIMEZONE=Asia/Kathmandu
```

Save and close the file (`Ctrl+X`, `Y`, `Enter` in nano).

---

## Step 5: Run the Bot

### 5.1 First Launch (Test Run)

Make sure your virtual environment is activated, then:

```bash
python bot.py
```

**✅ Success Output:**
```
Starting AI Learning Mentor Bot...
Configuration validated
Bot connected as AI Learning Mentor (ID: 123456789012345678)
Initializing state manager...
State manager initialized successfully
Cogs loaded: ['tracking', 'dashboard', 'admin']
Bot is ready!
```

**❌ Common Errors:**

| Error | Fix |
|-------|-----|
| `Invalid token` | Re-copy token from Discord Developer Portal |
| `State channel not found` | Verify STATE_CHANNEL_ID in .env |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Privilege Intent Error` | Enable intents in Developer Portal (Step 1.3) |

### 5.2 Verify Everything Works

After the bot starts, check these things in Discord:

| What to Check | Where | Expected Result |
|---------------|-------|-----------------|
| State message | `#🔒-bot-state` | Pinned message with JSON data |
| Dashboard | `#📊-dashboard` | Pinned embed showing "No data yet" |
| Commands | Type `/` anywhere | See bot commands in autocomplete |
| Test command | Type `/stats` | Shows your learning statistics |

### 5.3 First-Time Setup Complete! 🎉

Your bot is now running! Keep the terminal open to keep it active.

Press `Ctrl+C` to stop the bot when needed.

---

## Step 6: Run 24/7 as a Service (Linux)

To keep the bot running after you close the terminal, set up a systemd service.

### 6.1 Create the Service File

```bash
sudo nano /etc/systemd/system/learning-mentor-bot.service
```

Paste this (update the paths with your actual paths):

```ini
[Unit]
Description=AI Learning Mentor Discord Bot
After=network.target

[Service]
Type=simple
User=nischal
Group=nischal
WorkingDirectory=/home/nischal/Desktop/study-bot
Environment=PATH=/home/nischal/Desktop/study-bot/venv/bin
ExecStart=/home/nischal/Desktop/study-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> 💡 **Replace** `nischal` with your actual Linux username.
> 💡 **Replace** paths with your actual bot folder location.

Save and exit: `Ctrl+X`, `Y`, `Enter`

### 6.2 Enable and Start the Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable learning-mentor-bot

# Start the bot now
sudo systemctl start learning-mentor-bot
```

### 6.3 Manage the Service

```bash
# Check if it's running
sudo systemctl status learning-mentor-bot

# Stop the bot
sudo systemctl stop learning-mentor-bot

# Restart the bot
sudo systemctl restart learning-mentor-bot

# View live logs
sudo journalctl -u learning-mentor-bot -f

# View last 50 log lines
sudo journalctl -u learning-mentor-bot -n 50
```

### 6.4 Update the Bot

When you update bot files:

```bash
# Pull/copy new files, then:
sudo systemctl restart learning-mentor-bot
```

---

## 🛠️ Troubleshooting

### Bot Won't Start

| Symptom | Solution |
|---------|----------|
| `InvalidToken` error | Re-copy token from Developer Portal → Bot → Reset Token |
| `PrivilegedIntentsRequired` | Enable Message Content Intent in Developer Portal |
| `ModuleNotFoundError: No module named 'discord'` | Activate venv: `source venv/bin/activate` then `pip install -r requirements.txt` |
| Bot starts but goes offline | Check internet connection, Discord status at [discordstatus.com](https://discordstatus.com) |

### Channels/IDs Not Found

| Error | Solution |
|-------|----------|
| `State channel not found` | Verify STATE_CHANNEL_ID matches the actual channel |
| `Unknown Channel` | Bot lacks permission to see channel - check permissions |
| `Missing Access` | Re-invite bot with correct permissions (Step 1.4) |

### Commands Not Showing

1. Wait 5-10 minutes (Discord caches slash commands)
2. Try typing `/` in your server - commands should autocomplete
3. Verify bot has `applications.commands` scope (re-invite if needed)
4. Kick and re-invite the bot as a last resort

### Gemini API Issues

| Error | Solution |
|-------|----------|
| `API key not valid` | Re-copy key from Google AI Studio |
| `Quota exceeded` | You hit free tier limits - wait 24 hours |
| `Resource exhausted` | Too many requests - bot will use fallback responses |

### State/Data Issues

| Problem | Solution |
|---------|----------|
| State not saving | Bot needs "Manage Messages" permission in state channel |
| Data corruption | Use `/admin backup_state` then `/admin reset_day` |
| Duplicate streak loss | Check timezone setting in `.env` |

### Service Issues (Linux)

```bash
# Check what went wrong
sudo journalctl -u learning-mentor-bot -n 100

# Common fixes:
# Wrong path → Update paths in service file, then daemon-reload
# Permission denied → Check User/Group in service file
# Python not found → Use full path: /home/user/study-bot/venv/bin/python
```

---

## 📖 Daily Usage Guide

### For Users

1. **Log your learning** in `#📚-learning-logs` or your daily thread
   - Example: "Studied CNNs for 2 hours. Learned about convolution layers and pooling."
   - Minimum 30 characters to count as valid

2. **Check your progress**
   - `/stats` - View your points, streak, and level
   - `/streak` - See detailed streak information
   - `/badges` - View your earned badges

3. **View the leaderboard**
   - `/leaderboard` - Compare with your study partner

4. **Get AI feedback**
   - `/summary` - Request a weekly learning summary with AI insights

### For Admins

| Command | Purpose |
|---------|---------|
| `/admin health` | Diagnose bot issues |
| `/admin view_state` | See raw bot data |
| `/admin backup_state` | Create a backup thread |
| `/admin force_evaluate` | Trigger daily evaluation early |
| `/admin reset_day` | Reset today's logs (careful!) |

---

## 🎯 Tips for Success

1. **Be Consistent** - Log every day to build streaks
2. **Be Detailed** - More detail = more points + better AI feedback
3. **Use Threads** - Daily threads keep conversations organized
4. **Check Dashboard** - The dashboard updates with each evaluation

---

## 🆘 Getting Help

1. Check `bot.log` file in the bot folder for detailed errors
2. Run `/admin health` to diagnose common issues
3. Verify permissions in Discord server settings
4. Check that all required intents are enabled in Developer Portal

---

**Happy Learning! 🎓✨**

*Your AI Learning Mentor is now ready to help track your AI/ML/DL/DS journey!*
