# MCP-Compliant Slack Bot - Codebase Context

## Project Overview
Building an MCP (Model Context Protocol) compliant Slack bot that integrates with ClickUp and Supabase for intelligent client management and task operations.

## Current State
- **Status**: Implementation completed with false negative fix
- **Framework**: PACT (Prepare, Architect, Code, Test)
- **Current Phase**: 🧪 TEST (Ready for testing and deployment)
- **Recent Fix**: Increased max conversation iterations from 5 to 100 to prevent false negatives when tool chains succeed but hit iteration limits

## Architecture Goals
- **MCP Compliance**: Bot acts as MCP client with standardized tool interfaces
- **Slack Integration**: Natural language interaction via Socket Mode
- **Supabase Integration**: Client mapping database with detailed schema
- **ClickUp Integration**: Task management without full workspace hierarchy calls
- **LLM Orchestration**: GPT-4 for natural language understanding and tool selection
- **Deployment**: Railway hosting

## Key Requirements
1. **User Experience**: Ask about any client in any channel, get intelligent responses
2. **Edge Case Handling**: Extract client names from queries across channels
3. **Performance**: Avoid fetching entire workspace hierarchy (previous bottleneck)
4. **Security**: All credentials in environment variables, no hardcoded secrets

## Client Mapping Schema (Supabase)
```sql
client_mappings (
  id, client_name, clickup_project_name, clickup_folder_name, clickup_folder_id,
  clickup_list_name, clickup_list_id, slack_internal_channel_name, slack_internal_channel_id,
  slack_external_channel_name, slack_external_channel_id, alternatives, notes,
  created_at, updated_at, qa_list_name, qa_list_id, project_type,
  available_hours, revenue, average_delivery_hourly, status
)
```

## Available Credentials
- All credentials are stored securely in environment variables (.env file)
- Slack Bot Token: Available in SLACK_BOT_TOKEN
- Slack Socket Mode: Enabled via SLACK_APP_TOKEN
- Supabase Access: Available in SUPABASE_SERVICE_KEY and SUPABASE_URL
- ClickUp Integration: Available in CLICKUP_API_TOKEN and CLICKUP_TEAM_ID
- OpenAI API Key: Available in OPENAI_API_KEY

## Reference Implementations
- Existing ClickUp MCP Server: `/Users/v4lheru/Documents/Windows Files/MCP Server/clickup-mcp-server`
- Existing Supabase MCP Server: `/Users/v4lheru/Documents/Windows Files/MCP Server/supabase-mcp-server`

## Technology Stack
- **Language**: Python 3.10+
- **MCP Library**: `mcp` Python SDK
- **Slack SDK**: `slack_bolt` with Socket Mode
- **LLM**: OpenAI GPT-4 with function calling
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway
- **HTTP Client**: `httpx` for async operations

## Project Structure (Planned)
```
/
├── app.py                 # Main application entry point
├── codebase-context.md    # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore file
├── src/
│   ├── __init__.py
│   ├── slack_handler.py   # Slack event handling
│   ├── mcp_server.py     # MCP server with tools
│   ├── llm_orchestrator.py # GPT-4 integration and tool calling
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── supabase_tools.py  # Client mapping operations
│   │   ├── clickup_tools.py   # ClickUp task management
│   │   └── slack_tools.py     # Slack operations (optional)
│   └── utils/
│       ├── __init__.py
│       ├── config.py      # Configuration management
│       └── logger.py      # Logging setup
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_integration.py
└── Procfile              # Railway deployment config
```

## Security Considerations
- All API keys stored in environment variables
- .env file added to .gitignore
- Input validation for all tool parameters
- Rate limiting considerations for API calls
- Error handling to prevent credential exposure

## Performance Optimizations
- Client mapping cache to reduce Supabase calls
- Targeted ClickUp API calls using mapping data
- Async operations for concurrent API calls
- Connection pooling for database operations

## Next Steps
1. Set up project structure and dependencies
2. Implement MCP server with core tools
3. Create Slack bot integration with Socket Mode
4. Implement LLM orchestration with function calling
5. Add comprehensive error handling and logging
6. Test with real scenarios
7. Deploy to Railway

## Notes
- Previous implementation had performance issues with workspace hierarchy calls
- New approach uses client mapping for targeted operations
- MCP compliance ensures extensibility and maintainability
- Socket Mode eliminates need for public HTTP endpoints
