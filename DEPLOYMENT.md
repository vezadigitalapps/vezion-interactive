# Deployment Guide for MCP-Compliant Slack Bot

## 🚀 Quick Deployment to Railway

### 1. Prepare for Deployment

The bot is now ready for deployment. All dependencies are installed and configuration is validated.

### 2. Railway Setup

1. **Create Railway Account**: Go to [railway.app](https://railway.app) and sign up
2. **Connect GitHub**: Link your GitHub account to Railway
3. **Create New Project**: Click "New Project" → "Deploy from GitHub repo"
4. **Select Repository**: Choose your Slack bot repository

### 3. Environment Variables

In Railway dashboard, add these environment variables:

**SECURITY WARNING: Use your actual credentials from .env file. Never commit real credentials to git.**

```bash
# Slack Configuration
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_APP_TOKEN=your_slack_app_token_here
SLACK_SIGNING_SECRET=your_slack_signing_secret_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-1106-preview
OPENAI_TEMPERATURE=0.3

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# ClickUp Configuration
CLICKUP_API_TOKEN=your_clickup_api_token_here
CLICKUP_TEAM_ID=your_clickup_team_id_here

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
PORT=3000
```

### 4. Deploy

1. **Push to GitHub**: Commit and push your code
2. **Railway Auto-Deploy**: Railway will automatically detect the Python app and deploy
3. **Monitor Logs**: Check Railway logs for successful startup

### 5. Test Deployment

Once deployed:
1. Go to your Slack workspace
2. Mention the bot: `@bot what's the latest on Webconnex?`
3. Or send a DM: `what's happening with our clients?`

## 🧪 Local Testing

### Test the Bot Locally

```bash
# Start the bot
python3 app.py
