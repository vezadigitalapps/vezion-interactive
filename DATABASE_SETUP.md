# Database Setup Guide for MCP-Compliant Slack Bot

## 🗄️ Supabase Database Schema

This document contains the complete database schema and setup instructions for the Veza Digital AI Agent Slack bot.

## 📋 Required Tables

### 1. Client Mappings Table

```sql
CREATE TABLE client_mappings (
    id SERIAL PRIMARY KEY,
    client_name TEXT NOT NULL,
    clickup_project_name TEXT,
    clickup_folder_name TEXT,
    clickup_folder_id TEXT,
    clickup_list_name TEXT,
    clickup_list_id TEXT,
    slack_internal_channel_name TEXT,
    slack_internal_channel_id TEXT,
    slack_external_channel_name TEXT,
    slack_external_channel_id TEXT,
    alternatives TEXT[],
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    qa_list_name TEXT,
    qa_list_id TEXT,
    project_type TEXT,
    available_hours TEXT,
    revenue DECIMAL,
    average_delivery_hourly DECIMAL,
    status TEXT
);
```

### 2. Employees Table

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    real_name TEXT NOT NULL,
    slack_user_id TEXT UNIQUE NOT NULL,
    clickup_user_id TEXT NOT NULL,
    email TEXT,
    slack_username TEXT,
    clickup_username TEXT,
    clickup_role TEXT,
    clickup_color TEXT,
    clickup_initials TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 📊 Sample Data

### Client Mappings Example

```sql
INSERT INTO "public"."client_mappings" (
    "client_name", 
    "clickup_project_name", 
    "clickup_folder_name", 
    "clickup_folder_id", 
    "clickup_list_name", 
    "clickup_list_id", 
    "slack_internal_channel_name", 
    "slack_internal_channel_id", 
    "slack_external_channel_name", 
    "slack_external_channel_id", 
    "alternatives", 
    "project_type", 
    "available_hours", 
    "revenue", 
    "average_delivery_hourly", 
    "status"
) VALUES 
('Webconnex', 'Projects', 'Webconnex', '90154693297', 'Webconnex Tasks', '901507610577', '000-regfox-web', 'C02TG1Q7YCX', 'webconnex-x-veza', 'C02TG20HA2K', '{"RegFox","WebConnex"}', 'On-going', '55', '4200.00', '13.00', 'Active'),
('Clarity', 'Projects', 'Clarity', '90154755710', 'Clarity Tasks', '901507610501', '137-clarity-web', 'C07GNQB687P', 'clarity-x-veza', 'C07MJUGHDTQ', '{}', 'One-Time', '371', '55700.00', '23.71', 'Not Active'),
('Dialectica', 'Projects', 'Dialectica', '90154755710', 'Dialectica Tasks', '901507753477', '139-dialectica-web', 'C07MZNE8BKK', 'veza-x-dialectica', 'C07MJUGHDTQ', '{}', 'One-Time', '371', '55700.00', '23.71', 'Not Active');
```

### Employees Example

```sql
INSERT INTO "public"."employees" (
    "real_name", 
    "slack_user_id", 
    "clickup_user_id", 
    "email", 
    "slack_username", 
    "clickup_username", 
    "clickup_role", 
    "clickup_color", 
    "clickup_initials", 
    "is_active"
) VALUES 
('Stefan Katanic', 'UJFSERUCR', '10208217', 'stefan@vezadigital.com', 'Stefan Katanic', 'Stefan Katanic', 'owner', '#b388ff', 'SK', true),
('Marko Milutinovic', 'U02HU7JQ517', '42394425', 'marko.m@vezadigital.com', 'Marko Milutinovic', 'Marko Milutinovic', 'admin', '#81b1ff', 'MM', true),
('Dimitrije Janjic', 'U04LRJ2UM8D', '88760141', 'dimitrije@vezadigital.com', 'Dimitrije Janjic', 'Dimitrije Janjic', 'admin', '#006063', 'DJ', true),
('Julia Nicoloski', 'U01LN9D998S', '8730923', 'julia@vezadigital.com', 'Julia R. Nicoloski', 'Julia Nicoloski', 'member', '#b388ff', 'JN', true);
```

## 🔧 Database Indexes (Recommended)

```sql
-- Indexes for better performance
CREATE INDEX idx_client_mappings_channel_id ON client_mappings(slack_internal_channel_id);
CREATE INDEX idx_client_mappings_external_channel_id ON client_mappings(slack_external_channel_id);
CREATE INDEX idx_client_mappings_client_name ON client_mappings(client_name);
CREATE INDEX idx_employees_slack_user_id ON employees(slack_user_id);
CREATE INDEX idx_employees_clickup_user_id ON employees(clickup_user_id);
```

## 🔒 Row Level Security (RLS) Setup

```sql
-- Enable RLS on tables
ALTER TABLE client_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY "Enable all access for service role" ON client_mappings
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all access for service role" ON employees
    FOR ALL USING (auth.role() = 'service_role');
```

## 🚀 Railway Deployment Setup

### Environment Variables Required

**SECURITY NOTE: Never commit actual credentials to git. Use your actual values from .env file.**

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

### Railway Deployment Steps

1. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Connect your repository

2. **Set Environment Variables**
   - In Railway dashboard, go to Variables tab
   - Add all environment variables listed above
   - Set `ENVIRONMENT=production`

3. **Deploy Configuration**
   - Railway will automatically detect Python app
   - Uses `Procfile`: `web: python app.py`
   - Installs dependencies from `requirements.txt`

4. **Verify Deployment**
   - Check Railway logs for successful startup
   - Look for: "🚀 MCP-Compliant Slack Bot is now running!"
   - Verify: "15 MCP tools registered successfully"

## 🔍 Database Verification Queries

### Check Client Mappings
```sql
SELECT client_name, clickup_list_id, slack_internal_channel_id 
FROM client_mappings 
WHERE status = 'Active';
```

### Check Employees
```sql
SELECT real_name, slack_user_id, clickup_user_id 
FROM employees 
WHERE is_active = true;
```

### Verify Channel Mappings
```sql
SELECT client_name, slack_internal_channel_name, slack_internal_channel_id
FROM client_mappings 
WHERE slack_internal_channel_id IS NOT NULL;
```

## 🛠️ Bot Capabilities

### Client Management
- **Channel-based discovery**: Automatically identifies client from Slack channel
- **Fuzzy search**: Finds clients with partial names
- **Cross-channel queries**: Ask about any client from any channel
- **Client creation**: Add new clients with proper schema mapping

### Task Management
- **Task creation**: Create tasks with user assignment
- **Task updates**: Modify existing tasks
- **Recent activity**: Get tasks updated in timeframe
- **Time tracking**: Calculate hours from task details

### User Assignment
- **Slack → ClickUp mapping**: Maps Slack user mentions to ClickUp user IDs
- **Employee lookup**: Find team members by Slack ID
- **Task assignment**: Assign tasks to users via Slack mentions

### Executive Intelligence
- **Strategic insights**: Business analysis and recommendations
- **Executive reporting**: C-level focused summaries
- **Risk assessment**: Identify project risks and opportunities
- **Performance metrics**: Time, budget, and delivery insights

## 🎯 Usage Examples

### Client Queries
- `@bot what's the latest with Webconnex?`
- `@bot what are the active tasks here` (in client channel)
- `@bot show me recent activity for Clarity`

### Task Management
- `@bot create a task "Review proposal" for Webconnex`
- `@bot assign this task to @Marko Milutinovic`
- `@bot what tasks are assigned to John?`

### Time & Analytics
- `@bot how many hours spent on Webconnex this month?`
- `@bot analyze resource utilization for this project`

### Client Management
- `@bot add new client TechFlow Solutions with folder ID 90159029999`

## 🔧 Troubleshooting

### Common Issues

**Bot doesn't respond**
- Check Railway logs for errors
- Verify Slack tokens are correct
- Ensure bot is invited to channels

**Client not found**
- Verify client exists in client_mappings table
- Check channel ID mapping
- Use fuzzy search with partial names

**User assignment fails**
- Check employee exists in employees table
- Verify Slack user ID is correct
- Update employee mapping if needed

**Database connection issues**
- Verify Supabase URL and service key
- Check RLS policies allow service role access
- Ensure tables exist and have correct schema

## 📞 Support

The bot includes comprehensive logging and error handling. Check Railway logs for detailed debugging information.

**Ready for production deployment with complete database schema and Railway configuration!**
