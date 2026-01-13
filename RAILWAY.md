# Railway Deployment Guide

## Automatic Deployment (Recommended)

Railway will auto-detect your repository and deploy using the `Procfile`.

### Step 1: Push to Railway

If you deployed already, Railway will automatically redeploy when you push to GitHub.

### Step 2: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
DISCORD_TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id
STATE_CHANNEL_ID=your_state_channel_id
LEARNING_CHANNEL_ID=your_learning_channel_id
DASHBOARD_CHANNEL_ID=your_dashboard_channel_id
DAILY_THREADS_CHANNEL_ID=your_threads_channel_id
USER_IDS=user_id_1,user_id_2
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
TIMEZONE=Asia/Kathmandu
```

### Step 3: Deploy

Click **Deploy** and Railway will:
1. Detect Python 3.11 from `runtime.txt`
2. Install dependencies from `requirements.txt`
3. Run `python bot.py` as specified in `Procfile`

## Health Checks

Railway will automatically restart the bot if it crashes. You can also run:

```bash
python healthcheck.py
```

To verify configuration before deployment.

## Logs

View logs in Railway dashboard:
- Click on your service
- Go to **Deployments** tab
- Click on the latest deployment
- View real-time logs

## Troubleshooting

### Bot Not Starting

**Check logs for:**
- `Invalid Discord token!` → Reset token in Discord Developer Portal
- `Configuration errors` → Check environment variables match exactly
- `Cannot access guild` → Ensure bot is invited to your server

### Bot Goes Offline

Railway free tier gives 500 hours/month. If you need 24/7:
- Upgrade to paid plan ($5/month)
- Use Oracle Cloud Free Tier (always free)

### Commands Not Showing

- Wait 5-10 minutes for Discord to sync
- Kick and re-invite the bot
- Check bot has `applications.commands` scope

## Updating the Bot

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin main

# Railway auto-deploys!
```

## Cost

- **Free Tier**: 500 hours/month (~21 days)
- **Hobby Plan**: $5/month for 24/7 uptime
- **Pro Plan**: $20/month for multiple services

## Alternative: Oracle Cloud Free Tier

Forever free option with full 24/7 uptime:
1. Create Oracle Cloud account
2. Launch free VM (1GB RAM, always free)
3. SSH into VM and clone your repo
4. Run with systemd service

See [SETUP_GUIDE.md](../docs/SETUP_GUIDE.md) for detailed instructions.
