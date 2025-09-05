# MCP-Compliant Slack Bot for ClickUp Integration

A sophisticated Slack bot that uses the Model Context Protocol (MCP) to integrate with ClickUp and Supabase, providing intelligent client management and task operations through natural language interactions.

## 🚀 Features

- **Natural Language Processing**: Ask about any client in any Slack channel using GPT-4
- **MCP Compliance**: Standardized tool interfaces following Model Context Protocol
- **Intelligent Client Mapping**: Automatic client name extraction and mapping via Supabase
- **ClickUp Integration**: Create tasks, get updates, track time without workspace hierarchy overhead
- **Cross-Channel Support**: Ask about any client from any Slack channel
- **Socket Mode**: No public endpoints needed, secure WebSocket connection
- **Comprehensive Logging**: Structured logging with rich formatting for debugging

## 🏗️ Architecture

The bot follows the PACT framework (Prepare, Architect, Code, Test) and implements a clean MCP-compliant architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack User    │───▶│   Slack Handler  │───▶│ LLM Orchestrator│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ClickUp API   │◀───│   MCP Server     │◀───│   GPT-4 with    │
└─────────────────┘    │   (Tools)        │    │ Function Calling│
                       └──────────────────┘    └─────────────────┘
┌─────────────────┐              │
│  Supabase DB    │◀─────────────┘
└─────────────────┘
```

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **MCP Library**: `mcp` Python SDK with FastMCP
- **Slack SDK**: `slack_bolt` with Socket Mode
- **LLM**: OpenAI GPT-4 (gpt-4-1106-preview) with function calling
- **Database**: Supabase (PostgreSQL)
- **HTTP Client**: `httpx` for async operations
- **Logging**: `structlog` with `rich` formatting
- **Deployment**: Railway

## 📋 Prerequisites

1. **Slack App**: Create a Slack app with Socket Mode enabled
2. **Supabase Project**: Set up with client mapping table
3. **ClickUp API**: Personal or workspace API token
4. **OpenAI API**: GPT-4 access
5. **Railway Account**: For deployment (optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd slack-bot-mcp-clickup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `SLACK_APP_TOKEN`: Your Slack app token (xapp-...)
- `SLACK_SIGNING_SECRET`: Your Slack signing secret
- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Your Supabase service key
- `CLICKUP_API_TOKEN`: Your ClickUp API token
- `CLICKUP_TEAM_ID`: Your ClickUp team ID

### 3. Database Setup

Create the client mapping table in Supabase:

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

### 4. Run the Bot

```bash
python app.py
```

## 💬 Usage Examples

### Basic Queries
- `@bot what's the latest on Webconnex?`
- `@bot show me tasks updated this week for Client X`
- `@bot how many hours have we spent on Project Y?`

### Task Creation
- `@bot create a task to follow up with Client Z next week`
- `@bot add a task "Review proposal" for Webconnex`

### Direct Messages
You can also DM the bot directly without mentioning it:
- `what's happening with our clients this week?`
- `create a task for client onboarding`

## 🔧 Configuration

### Client Mapping
The bot uses Supabase to map client names to ClickUp resources. Each client should have:
- `client_name`: Primary client identifier
- `clickup_list_id`: Target ClickUp list for tasks
- `alternatives`: Array of alternative names/spellings

### Logging Levels
Set `LOG_LEVEL` in your environment:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only

### Cache Configuration
- `CACHE_TTL_SECONDS`: Client mapping cache duration (default: 300)

## 🚀 Deployment

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

The `Procfile` is already configured:
```
web: python app.py
```

### Manual Deployment

1. Set `ENVIRONMENT=production` in your environment
2. Ensure all required environment variables are set
3. Run `python app.py`

## 🧪 Testing

### Local Testing
1. Start the bot: `python app.py`
2. Check logs for successful initialization
3. Test in Slack by mentioning the bot
4. Verify database connections and API calls

### Example Test Scenarios
1. **Client Recognition**: Ask about a client that exists in your mapping
2. **Task Creation**: Request task creation with natural language
3. **Cross-Channel**: Ask about clients from different Slack channels
4. **Error Handling**: Try queries with non-existent clients

## 🔍 Troubleshooting

### Common Issues

**Bot doesn't respond in Slack**
- Check Socket Mode is enabled in Slack app settings
- Verify `SLACK_APP_TOKEN` and `SLACK_BOT_TOKEN` are correct
- Check bot is invited to the channel

**"Client not found" errors**
- Verify client exists in Supabase `client_mappings` table
- Check client name spelling and alternatives
- Review Supabase connection and credentials

**OpenAI API errors**
- Verify `OPENAI_API_KEY` is valid and has GPT-4 access
- Check API usage limits and billing
- Review model name in configuration

**ClickUp integration issues**
- Verify `CLICKUP_API_TOKEN` has required permissions
- Check `CLICKUP_TEAM_ID` is correct
- Ensure list IDs in client mapping are valid

### Debug Mode
Set `LOG_LEVEL=DEBUG` to see detailed logs including:
- MCP tool calls and responses
- LLM interactions and token usage
- API requests and responses
- Cache operations

## 🏗️ Architecture Details

### MCP Tools Available
- `get_client_mapping`: Retrieve client information from Supabase
- `search_client_mappings`: Fuzzy search for clients
- `get_all_client_names`: List all available clients
- `get_tasks_by_list_id`: Fetch tasks from ClickUp list
- `get_tasks_updated_since`: Get recently updated tasks
- `create_task`: Create new ClickUp task
- `update_task`: Modify existing task
- `get_task_details`: Get comprehensive task information
- `get_time_tracking`: Retrieve time tracking data

### Security Features
- All credentials stored in environment variables
- Input validation on all tool parameters
- Rate limiting considerations
- Error handling prevents credential exposure
- Supabase RLS (Row Level Security) support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the PACT framework principles
4. Add comprehensive logging
5. Test thoroughly
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with the Model Context Protocol (MCP) by Anthropic
- Inspired by modern AI-assisted development practices
- Uses the PACT framework for systematic development
