#!/usr/bin/env python3
"""
Railway-optimized startup script for MCP-compliant Slack Bot.

This script provides enhanced startup handling, logging, and error recovery
specifically optimized for Railway deployment environment.
"""

import os
import sys
import asyncio
import signal
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure basic logging before importing our modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def setup_railway_environment():
    """Setup Railway-specific environment configurations."""
    
    # Railway provides PORT environment variable
    port = os.getenv('PORT', '3000')
    os.environ.setdefault('PORT', port)
    
    # Ensure production environment on Railway
    if not os.getenv('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'production'
    
    # Set Python-specific optimizations
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONPATH'] = '/app'
    
    logger.info(f"Railway environment configured - Port: {port}")

def validate_required_env_vars():
    """Validate that all required environment variables are present."""
    
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN', 
        'SLACK_SIGNING_SECRET',
        'OPENAI_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'CLICKUP_API_TOKEN',
        'CLICKUP_TEAM_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables in Railway dashboard")
        sys.exit(1)
    
    logger.info("All required environment variables are present")

async def main():
    """Main application entry point with Railway optimizations."""
    
    try:
        # Setup Railway environment
        setup_railway_environment()
        
        # Validate environment variables
        validate_required_env_vars()
        
        # Import and run the main application
        logger.info("🚀 Starting MCP-compliant Slack Bot on Railway...")
        
        # Import here to ensure environment is set up first
        from app import main as app_main
        
        # Run the main application
        await app_main()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        # In Railway, we want to exit with error code so it can restart
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
