"""
Slack Bot Handler for MCP Integration.

This module handles all Slack interactions, including event processing,
message handling, and integration with the LLM orchestrator.
"""

import asyncio
import re
from typing import Dict, Any, Optional
from datetime import datetime

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .llm_orchestrator import get_llm_orchestrator
from .utils import get_logger, log_slack_event, get_config

logger = get_logger(__name__)
config = get_config()


class SlackBotHandler:
    """
    Handles Slack bot interactions and integrates with MCP tools via LLM orchestrator.
    """
    
    def __init__(self):
        # Initialize Slack app with Socket Mode
        self.app = AsyncApp(
            token=config.slack_bot_token,
            signing_secret=config.slack_signing_secret
        )
        
        # Socket mode handler will be initialized in async context
        self.handler = None
        
        # Web client for additional API calls
        self.client = AsyncWebClient(token=config.slack_bot_token)
        
        # Thread context cache to maintain conversation history
        self.thread_contexts = {}
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("Slack bot handler initialized")
    
    def _register_handlers(self):
        """Register all Slack event handlers."""
        
        # Handle app mentions (when bot is mentioned in channels)
        @self.app.event("app_mention")
        async def handle_app_mention(event, say, ack):
            await ack()
            logger.info("App mention received", **log_slack_event("app_mention", event.get("user"), event.get("channel")))
            
            try:
                # Extract message text and remove bot mention
                text = event.get("text", "")
                user_id = event.get("user")
                channel_id = event.get("channel")
                thread_ts = event.get("thread_ts") or event.get("ts")  # MANDATORY: Always use thread
                
                # Remove bot mention from text
                clean_text = self._clean_message_text(text)
                
                if not clean_text.strip():
                    await say("Hi! How can I help you with your ClickUp projects today?", thread_ts=thread_ts)
                    return
                
                # Send immediate loading indicator in thread
                loading_msg = await say(":loading: *Processing your request...* Please wait while I analyze the data.", thread_ts=thread_ts)
                
                try:
                    # Process message with LLM orchestrator (with thread context)
                    response = await self._process_message(clean_text, user_id, channel_id, thread_ts)
                    
                    # Update the loading message with the actual response
                    await self.client.chat_update(
                        channel=channel_id,
                        ts=loading_msg["ts"],
                        text=response
                    )
                except Exception as update_error:
                    logger.warning("Failed to update loading message, sending new message", error=str(update_error))
                    # Fallback: send new message if update fails
                    await say(response, thread_ts=thread_ts)
                
            except Exception as e:
                logger.error("Error handling app mention", error=str(e), event=event)
                await say("I apologize, but I encountered an error processing your request. Please try again.", thread_ts=event.get("thread_ts") or event.get("ts"))
        
        # Handle thread messages where bot was previously mentioned
        @self.app.event("message")
        async def handle_thread_message(event, say, ack):
            await ack()
            
            # Ignore bot messages, file shares, and non-thread messages
            if (event.get("bot_id") or 
                event.get("subtype") == "bot_message" or 
                event.get("subtype") == "file_share" or
                not event.get("thread_ts")):
                return
            
            thread_ts = event.get("thread_ts")
            
            # Only handle thread messages where bot was previously mentioned
            try:
                # Get thread history to see if bot was mentioned in the thread
                thread_history = await self.client.conversations_replies(
                    channel=event.get("channel"),
                    ts=thread_ts,
                    limit=50
                )
                
                # Check if bot was mentioned in any message in the thread OR if bot has replied in the thread
                bot_in_thread = False
                for msg in thread_history.get("messages", []):
                    # Check for bot mentions or bot messages
                    if (msg.get("text", "").find("<@U08S70BV201>") != -1 or  # Bot user ID
                        msg.get("bot_id") or 
                        msg.get("user") == "U08S70BV201"):  # Bot user ID
                        bot_in_thread = True
                        break
                
                if bot_in_thread:
                    logger.info("Thread message received", **log_slack_event("thread_message", event.get("user"), event.get("channel")))
                    
                    text = event.get("text", "")
                    user_id = event.get("user")
                    channel_id = event.get("channel")
                    
                    if text.strip():
                        # Send loading indicator
                        loading_msg = await say(":loading: *Processing your follow-up...* Analyzing with context.", thread_ts=thread_ts)
                        
                        try:
                            # Process message with LLM orchestrator (with thread context)
                            response = await self._process_message(text, user_id, channel_id, thread_ts)
                            
                            # Update loading message with response
                            await self.client.chat_update(
                                channel=channel_id,
                                ts=loading_msg["ts"],
                                text=response
                            )
                        except Exception as update_error:
                            logger.warning("Failed to update loading message in thread, sending new message", error=str(update_error))
                            # Fallback: send new message if update fails
                            await say(response, thread_ts=thread_ts)
            
            except Exception as e:
                logger.error("Error handling thread message", error=str(e), event=event)
        
        # Handle slash commands (optional)
        @self.app.command("/clickup")
        async def handle_clickup_command(ack, respond, command):
            await ack()
            logger.info("Slash command received", **log_slack_event("slash_command", command.get("user_id"), command.get("channel_id")))
            
            try:
                text = command.get("text", "")
                user_id = command.get("user_id")
                channel_id = command.get("channel_id")
                
                if not text.strip():
                    await respond("Usage: `/clickup [your question about ClickUp projects]`\n\nExample: `/clickup what's the latest on Client X?`")
                    return
                
                # Process message with LLM orchestrator
                response = await self._process_message(text, user_id, channel_id)
                
                # Send response
                await respond(response)
                
            except Exception as e:
                logger.error("Error handling slash command", error=str(e), command=command)
                await respond("I apologize, but I encountered an error processing your command. Please try again.")
        
        # Handle errors
        @self.app.error
        async def global_error_handler(error, body):
            logger.error("Global Slack error", error=str(error), body=body)
            return "Sorry, something went wrong. Please try again."
        
        logger.info("All Slack event handlers registered")
    
    def _clean_message_text(self, text: str) -> str:
        """
        Clean message text by removing bot mentions and extra whitespace.
        """
        # Remove bot mentions (format: <@U1234567890>)
        text = re.sub(r'<@U[A-Z0-9]+>', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    async def _process_message(self, text: str, user_id: str, channel_id: str, thread_ts: str = None) -> str:
        """
        Process a message using the LLM orchestrator with thread context.
        """
        logger.debug("Processing message", text=text[:100], user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)
        
        try:
            # Get additional context about the channel
            context = await self._get_channel_context(channel_id)
            
            # Add thread context if available
            if thread_ts:
                thread_context = await self._get_thread_context(channel_id, thread_ts)
                context.update(thread_context)
            
            # Get LLM orchestrator and process message
            orchestrator = await get_llm_orchestrator()
            response = await orchestrator.process_user_message(
                user_message=text,
                user_id=user_id,
                channel_id=channel_id,
                context=context
            )
            
            # Store the conversation in thread context for future reference
            if thread_ts:
                self._update_thread_context(channel_id, thread_ts, text, response)
            
            return response
            
        except Exception as e:
            logger.error("Error processing message", error=str(e), text=text[:100])
            raise
    
    async def _get_thread_context(self, channel_id: str, thread_ts: str) -> Dict[str, Any]:
        """
        Get the conversation context from a thread with enhanced memory.
        """
        try:
            # Get thread history
            thread_history = await self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=30  # More messages for better context
            )
            
            messages = thread_history.get("messages", [])
            
            # Extract detailed conversation history
            conversation_history = []
            task_context = {}
            client_context = {}
            
            for msg in messages:
                user_text = msg.get("text", "")
                timestamp = msg.get("ts", "")
                
                if not msg.get("bot_id"):  # User message
                    if user_text:
                        conversation_history.append(f"User: {user_text}")
                        
                        # Extract task-related context
                        if "task" in user_text.lower():
                            if "create" in user_text.lower():
                                task_context["last_task_creation"] = user_text
                            if "assign" in user_text.lower():
                                task_context["last_assignment"] = user_text
                            if "time" in user_text.lower() or "hour" in user_text.lower():
                                task_context["time_tracking_request"] = user_text
                        
                        # Extract client context
                        if any(client in user_text.lower() for client in ["tesorai", "tesor", "client"]):
                            client_context["mentioned_client"] = "TesorAI"
                            client_context["client_context"] = user_text
                
                elif msg.get("bot_id"):  # Bot message
                    if user_text:
                        conversation_history.append(f"Bot: {user_text[:300]}...")  # More context from bot
                        
                        # Extract successful actions from bot responses
                        if "successfully created" in user_text.lower():
                            task_context["last_successful_creation"] = user_text
                        if "task link" in user_text.lower() or "clickup" in user_text.lower():
                            task_context["has_task_link"] = True
            
            # Build comprehensive context
            context = {
                "thread_context": True,
                "conversation_history": "\n".join(conversation_history[-8:]),  # Last 8 exchanges
                "task_context": task_context,
                "client_context": client_context,
                "thread_ts": thread_ts,
                "channel_id": channel_id
            }
            
            # Add specific context hints for the LLM
            if task_context.get("last_successful_creation") and task_context.get("time_tracking_request"):
                context["action_needed"] = "time_tracking_for_existing_task"
                context["hint"] = "User is asking to add time tracking to a task that was just created in this thread"
            
            if client_context.get("mentioned_client"):
                context["active_client"] = client_context["mentioned_client"]
                context["hint"] = f"User is working with {client_context['mentioned_client']} in this conversation"
            
            return context
            
        except Exception as e:
            logger.error("Error getting thread context", channel_id=channel_id, thread_ts=thread_ts, error=str(e))
            return {}
    
    def _update_thread_context(self, channel_id: str, thread_ts: str, user_message: str, bot_response: str):
        """
        Update the thread context cache.
        """
        thread_key = f"{channel_id}:{thread_ts}"
        
        if thread_key not in self.thread_contexts:
            self.thread_contexts[thread_key] = {
                "created_at": datetime.now(),
                "messages": []
            }
        
        # Add the exchange to context
        self.thread_contexts[thread_key]["messages"].append({
            "user_message": user_message,
            "bot_response": bot_response[:200],  # Truncate for memory
            "timestamp": datetime.now()
        })
        
        # Keep only last 10 exchanges per thread
        if len(self.thread_contexts[thread_key]["messages"]) > 10:
            self.thread_contexts[thread_key]["messages"] = self.thread_contexts[thread_key]["messages"][-10:]
    
    async def _get_channel_context(self, channel_id: str) -> Dict[str, Any]:
        """
        Get additional context about the Slack channel.
        """
        try:
            # Get channel info
            channel_info = await self.client.conversations_info(channel=channel_id)
            
            context = {
                "channel_id": channel_id,
                "channel_name": channel_info.get("channel", {}).get("name"),
                "channel_type": channel_info.get("channel", {}).get("is_channel", False),
                "is_private": channel_info.get("channel", {}).get("is_private", False)
            }
            
            return context
            
        except SlackApiError as e:
            logger.warning("Could not get channel context", channel_id=channel_id, error=str(e))
            return {}
        except Exception as e:
            logger.error("Error getting channel context", channel_id=channel_id, error=str(e))
            return {}
    
    async def send_message(self, channel: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        This method can be used programmatically to send messages.
        """
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                **kwargs
            )
            
            logger.info("Message sent successfully", channel=channel, text=text[:100])
            return response.data
            
        except SlackApiError as e:
            logger.error("Failed to send Slack message", channel=channel, error=str(e))
            raise
    
    async def update_message(self, channel: str, ts: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing Slack message.
        """
        try:
            response = await self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                **kwargs
            )
            
            logger.info("Message updated successfully", channel=channel, ts=ts)
            return response.data
            
        except SlackApiError as e:
            logger.error("Failed to update Slack message", channel=channel, ts=ts, error=str(e))
            raise
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get information about a Slack user.
        """
        try:
            response = await self.client.users_info(user=user_id)
            return response.data.get("user", {})
            
        except SlackApiError as e:
            logger.warning("Could not get user info", user_id=user_id, error=str(e))
            return {}
    
    async def start(self):
        """
        Start the Slack bot using Socket Mode.
        """
        logger.info("Starting Slack bot with Socket Mode")
        
        try:
            # Test the connection
            auth_response = await self.client.auth_test()
            bot_user_id = auth_response.get("user_id")
            bot_name = auth_response.get("user")
            
            logger.info("Slack bot authenticated successfully", 
                       bot_user_id=bot_user_id, 
                       bot_name=bot_name)
            
            # Initialize socket mode handler in async context
            if self.handler is None:
                self.handler = AsyncSocketModeHandler(
                    self.app, 
                    config.slack_app_token
                )
            
            # Start the socket mode handler
            await self.handler.start_async()
            
        except Exception as e:
            logger.error("Failed to start Slack bot", error=str(e))
            raise
    
    async def stop(self):
        """
        Stop the Slack bot and clean up resources.
        """
        logger.info("Stopping Slack bot")
        
        try:
            # Close the socket mode handler
            await self.handler.close_async()
            
            # Close the web client
            await self.client.close()
            
            logger.info("Slack bot stopped successfully")
            
        except Exception as e:
            logger.error("Error stopping Slack bot", error=str(e))


# Global Slack bot handler instance will be created in async context
slack_handler = None


async def get_slack_handler() -> SlackBotHandler:
    """Get the global Slack bot handler instance."""
    global slack_handler
    if slack_handler is None:
        slack_handler = SlackBotHandler()
    return slack_handler


async def start_slack_bot():
    """Start the Slack bot."""
    handler = await get_slack_handler()
    await handler.start()


async def stop_slack_bot():
    """Stop the Slack bot."""
    handler = await get_slack_handler()
    await handler.stop()
