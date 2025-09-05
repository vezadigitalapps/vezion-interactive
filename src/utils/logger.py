"""
Structured logging setup for the MCP Slack Bot.

This module provides a centralized logging configuration using structlog
for better observability and debugging.
"""

import sys
import logging
from typing import Any, Dict
import structlog
from rich.console import Console
from rich.logging import RichHandler

from .config import get_config

config = get_config()


def setup_logging() -> structlog.stdlib.BoundLogger:
    """
    Set up structured logging with rich formatting for development
    and JSON formatting for production.
    """
    
    # Configure standard library logging
    if config.environment == "development":
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, config.log_level),
            handlers=[
                RichHandler(
                    console=Console(stderr=True),
                    show_time=True,
                    show_path=True,
                    markup=True,
                    rich_tracebacks=True,
                )
            ]
        )
    else:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, config.log_level)
        )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if config.environment == "development":
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:
        processors.extend([
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with optional name."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def log_function_call(func_name: str, **kwargs) -> Dict[str, Any]:
    """Helper to log function calls with parameters."""
    return {
        "function": func_name,
        "parameters": {k: v for k, v in kwargs.items() if not k.startswith('_')}
    }


def log_api_call(service: str, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Helper to log API calls."""
    return {
        "api_call": True,
        "service": service,
        "endpoint": endpoint,
        "method": method,
        **kwargs
    }


def log_mcp_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to log MCP tool calls."""
    return {
        "mcp_tool": tool_name,
        "arguments": arguments,
        "type": "tool_call"
    }


def log_slack_event(event_type: str, user_id: str = None, channel_id: str = None, **kwargs) -> Dict[str, Any]:
    """Helper to log Slack events."""
    return {
        "slack_event": event_type,
        "user_id": user_id,
        "channel_id": channel_id,
        **kwargs
    }


def log_llm_interaction(model: str, prompt_tokens: int = None, completion_tokens: int = None, **kwargs) -> Dict[str, Any]:
    """Helper to log LLM interactions."""
    return {
        "llm_interaction": True,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        **kwargs
    }


# Initialize logging on module import
logger = setup_logging()
