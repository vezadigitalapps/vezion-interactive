"""
Slack Message Tools for querying Slack channel messages from Supabase.

This module provides tools to query the slack-channels-messages table
to retrieve client messages and conversation history.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..utils import get_logger, log_function_call, get_config

logger = get_logger(__name__)
config = get_config()


class SlackMessageTools:
    """Tools for querying Slack messages from Supabase."""
    
    def __init__(self):
        from supabase import create_client, Client
        self.client: Client = create_client(
            config.supabase_url,
            config.supabase_service_key
        )
    
    async def get_recent_messages_by_channel(
        self, 
        channel_id: str, 
        limit: int = 10,
        hours_ago: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from a specific Slack channel.
        
        Args:
            channel_id: The Slack channel ID
            limit: Maximum number of messages to return (default 10)
            hours_ago: Only get messages from the last N hours (optional)
        
        Returns:
            List of message dictionaries with user, text, and timestamp
        """
        logger.info("Getting recent messages by channel", 
                   **log_function_call("get_recent_messages_by_channel", 
                                      channel_id=channel_id, 
                                      limit=limit,
                                      hours_ago=hours_ago))
        
        try:
            query = self.client.table("slack-channels-messages").select("*").eq("channel_id", channel_id)
            
            # Filter by time if specified
            if hours_ago:
                cutoff_time = datetime.now() - timedelta(hours=hours_ago)
                query = query.gte("timestamp", cutoff_time.isoformat())
            
            # Order by timestamp descending and limit
            response = query.order("timestamp", desc=True).limit(limit).execute()
            
            messages = response.data or []
            logger.info("Successfully retrieved messages", 
                       channel_id=channel_id, 
                       message_count=len(messages))
            
            return messages
            
        except Exception as e:
            logger.error("Error retrieving messages by channel", 
                        channel_id=channel_id, 
                        error=str(e))
            raise Exception(f"Failed to retrieve messages for channel {channel_id}: {str(e)}")
    
    async def get_latest_client_message(self, channel_id: str) -> Dict[str, Any]:
        """
        Get the most recent message from a client in a specific channel.
        
        CRITICAL: Clients are external users with user_id but user_name = NULL
        Employees have both user_id AND user_name populated.
        This filters to show only client messages (user_name IS NULL).
        
        Args:
            channel_id: The Slack channel ID
        
        Returns:
            Dictionary with the latest client message details
        """
        logger.info("Getting latest client message", 
                   **log_function_call("get_latest_client_message", channel_id=channel_id))
        
        try:
            # Get recent messages from CLIENTS ONLY (user_name is NULL for external users)
            # Clients have user_id but no user_name because they're external connections
            response = self.client.table("slack-channels-messages")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .is_("user_name", "null")\
                .not_.is_("message_text", "null")\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                message = response.data[0]
                logger.info("Successfully retrieved latest client message", 
                           channel_id=channel_id,
                           timestamp=message.get("timestamp"),
                           has_user_id=bool(message.get("user_id")))
                return message
            else:
                logger.warning("No client messages found", channel_id=channel_id)
                return {}
                
        except Exception as e:
            logger.error("Error retrieving latest client message", 
                        channel_id=channel_id, 
                        error=str(e))
            raise Exception(f"Failed to retrieve latest client message for channel {channel_id}: {str(e)}")
    
    async def search_messages_by_text(
        self, 
        channel_id: str, 
        search_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for messages containing specific text in a channel.
        
        Args:
            channel_id: The Slack channel ID
            search_text: Text to search for in messages
            limit: Maximum number of messages to return
        
        Returns:
            List of matching message dictionaries
        """
        logger.info("Searching messages by text", 
                   **log_function_call("search_messages_by_text", 
                                      channel_id=channel_id,
                                      search_text=search_text,
                                      limit=limit))
        
        try:
            response = self.client.table("slack-channels-messages")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .ilike("message_text", f"%{search_text}%")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = response.data or []
            logger.info("Successfully searched messages", 
                       channel_id=channel_id,
                       search_text=search_text,
                       result_count=len(messages))
            
            return messages
            
        except Exception as e:
            logger.error("Error searching messages", 
                        channel_id=channel_id,
                        search_text=search_text,
                        error=str(e))
            raise Exception(f"Failed to search messages in channel {channel_id}: {str(e)}")
    
    async def get_conversation_context(
        self, 
        channel_id: str,
        hours_ago: int = 24,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get conversation context from a channel including message statistics.
        
        Properly separates client messages (user_name IS NULL) from employee messages.
        
        Args:
            channel_id: The Slack channel ID
            hours_ago: Look back this many hours
            limit: Maximum number of messages to analyze
        
        Returns:
            Dictionary with conversation summary and recent messages
        """
        logger.info("Getting conversation context", 
                   **log_function_call("get_conversation_context",
                                      channel_id=channel_id,
                                      hours_ago=hours_ago))
        
        try:
            messages = await self.get_recent_messages_by_channel(
                channel_id=channel_id,
                limit=limit,
                hours_ago=hours_ago
            )
            
            # Analyze messages - CRITICAL: Clients have user_name = NULL
            # Clients: user_id exists but user_name is NULL (external users)
            # Employees: both user_id and user_name exist
            client_messages = [m for m in messages if m.get("user_name") is None and m.get("message_text")]
            employee_messages = [m for m in messages if m.get("user_name") is not None and m.get("user_name") != "VEZION" and m.get("message_text")]
            bot_messages = [m for m in messages if m.get("user_name") == "VEZION"]
            
            context = {
                "channel_id": channel_id,
                "total_messages": len(messages),
                "client_messages_count": len(client_messages),
                "employee_messages_count": len(employee_messages),
                "bot_messages_count": len(bot_messages),
                "latest_client_message": client_messages[0] if client_messages else None,
                "latest_employee_message": employee_messages[0] if employee_messages else None,
                "recent_client_messages": client_messages[:5],  # Last 5 client messages
                "recent_employee_messages": employee_messages[:5],  # Last 5 employee messages
                "recent_messages": messages[:10],  # Last 10 messages overall
                "time_range_hours": hours_ago
            }
            
            logger.info("Successfully built conversation context",
                       channel_id=channel_id,
                       total_messages=len(messages),
                       client_count=len(client_messages),
                       employee_count=len(employee_messages))
            
            return context
            
        except Exception as e:
            logger.error("Error getting conversation context",
                        channel_id=channel_id,
                        error=str(e))
            raise Exception(f"Failed to get conversation context for channel {channel_id}: {str(e)}")


# Global instance
slack_message_tools = SlackMessageTools()


# MCP Tool Functions
async def get_recent_messages_by_channel(
    channel_id: str, 
    limit: int = 10,
    hours_ago: Optional[int] = None
) -> List[Dict[str, Any]]:
    """MCP tool: Get recent messages from a Slack channel."""
    return await slack_message_tools.get_recent_messages_by_channel(channel_id, limit, hours_ago)


async def get_latest_client_message(channel_id: str) -> Dict[str, Any]:
    """MCP tool: Get the most recent client message from a channel."""
    return await slack_message_tools.get_latest_client_message(channel_id)


async def search_messages_by_text(
    channel_id: str, 
    search_text: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """MCP tool: Search for messages containing specific text."""
    return await slack_message_tools.search_messages_by_text(channel_id, search_text, limit)


async def get_conversation_context(
    channel_id: str,
    hours_ago: int = 24,
    limit: int = 20
) -> Dict[str, Any]:
    """MCP tool: Get conversation context and statistics from a channel."""
    return await slack_message_tools.get_conversation_context(channel_id, hours_ago, limit)
