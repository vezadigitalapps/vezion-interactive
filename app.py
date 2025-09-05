"""
Main Application Entry Point for MCP-Compliant Slack Bot.

This is the main entry point that starts the Slack bot with all MCP integrations.
"""

import asyncio
import signal
import sys
from typing import Optional

from src.slack_handler import start_slack_bot, stop_slack_bot
from src.mcp_server import get_mcp_server
from src.llm_orchestrator import get_llm_orchestrator
from src.utils import get_logger, get_config, is_production

logger = get_logger(__name__)
config = get_config()


class SlackBotApplication:
    """Main application class that manages the lifecycle of all components."""
    
    def __init__(self):
        self.running = False
        self._shutdown_event = asyncio.Event()
    
    async def startup(self):
        """Initialize and start all application components."""
        logger.info("🛠️ Starting MCP-Compliant Slack Bot", environment=config.environment)
        
        try:
            # Initialize MCP server
            logger.info("Initializing MCP server...")
            mcp_server = await get_mcp_server()
            tool_count = len(mcp_server.get_tool_schemas())
            logger.info("MCP server initialized", tool_count=tool_count)
            
            # Initialize LLM orchestrator
            logger.info("Initializing LLM orchestrator...")
            orchestrator = await get_llm_orchestrator()
            logger.info("LLM orchestrator initialized", model=config.openai_model)
            
            # Start Slack bot
            logger.info("Starting Slack bot...")
            await start_slack_bot()
            logger.info("Slack bot started successfully")
            
            self.running = True
            logger.info("🚀 MCP-Compliant Slack Bot is now running!")
            
            if not is_production():
                logger.info("Bot is ready to receive messages in Slack!")
                logger.info("Try mentioning the bot in a channel or sending a direct message")
                logger.info("Example: '@bot what's the latest on Webconnex?'")
            
        except Exception as e:
            logger.error("Failed to start application", error=str(e))
            raise
    
    async def shutdown(self):
        """Gracefully shutdown all application components."""
        if not self.running:
            return
        
        logger.info("🛑 Shutting down MCP-Compliant Slack Bot...")
        
        try:
            # Stop Slack bot
            logger.info("Stopping Slack bot...")
            await stop_slack_bot()
            
            # Close LLM orchestrator
            logger.info("Closing LLM orchestrator...")
            orchestrator = await get_llm_orchestrator()
            await orchestrator.close()
            
            # Close MCP server
            logger.info("Closing MCP server...")
            mcp_server = await get_mcp_server()
            await mcp_server.close()
            
            self.running = False
            logger.info("✅ Application shutdown completed")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    async def run(self):
        """Run the application with proper signal handling."""
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start the application
            await self.startup()
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error("Application error", error=str(e))
            raise
        finally:
            # Always attempt cleanup
            await self.shutdown()


async def main():
    """Main entry point."""
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        
        # Check required environment variables
        required_vars = [
            "SLACK_BOT_TOKEN",
            "SLACK_APP_TOKEN", 
            "SLACK_SIGNING_SECRET",
            "OPENAI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "CLICKUP_API_TOKEN",
            "CLICKUP_TEAM_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(config, var.lower(), None):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error("Missing required environment variables", missing_vars=missing_vars)
            logger.error("Please check your .env file or environment configuration")
            sys.exit(1)
        
        logger.info("Configuration validated successfully")
        
        # Create and run application
        app = SlackBotApplication()
        await app.run()
        
    except Exception as e:
        logger.error("Fatal application error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error("Unhandled exception", error=str(e))
        sys.exit(1)
