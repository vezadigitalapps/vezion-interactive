# Railway Deployment Guide

## 🚀 Quick Railway Deployment

This guide provides step-by-step instructions for deploying the MCP-compliant Slack Bot to Railway.

## 📋 Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub repository with the bot code
- Environment variables from your `.env` file

## 🔧 Deployment Files

The following files are configured for Railway deployment:

- **`Procfile`**: Defines the web process command
- **`railway.json`**: Railway-specific configuration
- **`nixpacks.toml`**: Build configuration for Python 3.10
- **`start.py`**: Railway-optimized startup script
- **`requirements.txt`**: All Python dependencies

## 🚀 Deployment Steps

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository: `vezadigitalapps/vezion-interactive`

### 2. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

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

### 3. Deploy

1. Railway will automatically detect the Python app
2. It will use `nixpacks.toml` for build configuration
3. Dependencies will be installed from `requirements.txt`
4. The app will start using `start.py` (defined in `Procfile`)

### 4. Monitor Deployment

1. Check the **Deployments** tab for build progress
2. View **Logs** tab for startup messages
3. Look for: `🚀 Starting MCP-compliant Slack Bot on Railway...`
4. Verify: `All required environment variables are present`

## 🔍 Troubleshooting

### Common Issues

**Build Failures**
- Check that all dependencies in `requirements.txt` are available
- Verify Python 3.10 compatibility
- Review build logs in Railway dashboard

**Environment Variable Errors**
- Ensure all required variables are set in Railway dashboard
- Check variable names match exactly (case-sensitive)
- Verify no extra spaces in variable values

**Startup Failures**
- Check application logs in Railway dashboard
- Verify Slack tokens are valid and have correct permissions
- Ensure Supabase and ClickUp credentials are correct

**Bot Not Responding**
- Verify Slack app has Socket Mode enabled
- Check that bot is invited to channels
- Ensure OpenAI API key has GPT-4 access

### Debug Commands

View logs in Railway dashboard or use Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and view logs
railway login
railway logs
```

## 🎯 Expected Startup Sequence

1. **Environment Setup**: Railway environment configured
2. **Variable Validation**: All required environment variables present
3. **MCP Server Init**: MCP server initialized with tools
4. **LLM Orchestrator**: OpenAI GPT-4 connection established
5. **Slack Bot Start**: Socket Mode connection established
6. **Ready**: Bot ready to receive messages

## 📊 Performance Monitoring

Railway provides built-in monitoring:

- **CPU Usage**: Monitor application performance
- **Memory Usage**: Track memory consumption
- **Network**: Monitor API calls and responses
- **Logs**: Real-time application logs

## 🔄 Updates and Redeployment

To update the bot:

1. Push changes to GitHub repository
2. Railway will automatically redeploy
3. Monitor deployment logs
4. Test bot functionality after deployment

## 🛡️ Security Notes

- All sensitive data is stored in Railway environment variables
- No credentials are committed to the repository
- Railway provides secure environment isolation
- All API communications use HTTPS/WSS

## 📞 Support

If you encounter issues:

1. Check Railway deployment logs
2. Verify all environment variables are set correctly
3. Test individual API connections (Slack, OpenAI, Supabase, ClickUp)
4. Review the troubleshooting section above

**The bot is now ready for production deployment on Railway!**
