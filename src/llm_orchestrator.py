"""
LLM Orchestrator for MCP Tool Integration.

This module handles the interaction with OpenAI's GPT-4 API, including
function calling to execute MCP tools based on user queries.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import openai
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from .mcp_server import get_mcp_server
from .utils import get_logger, log_llm_interaction, get_config

logger = get_logger(__name__)
config = get_config()


class LLMOrchestrator:
    """
    Orchestrates LLM interactions with MCP tools for intelligent responses.
    
    This class handles the conversation flow between user queries, GPT-4,
    and MCP tool execution, providing a seamless AI-powered experience.
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        self.temperature = config.openai_temperature
        self.max_iterations = 100  # Allow more iterations to complete complex tool chains
        
        # Base system prompt (date will be added dynamically)
        self.base_system_prompt = """You are the *Veza Digital AI Agent*, an intelligent assistant that helps C-level executives and leadership teams manage ClickUp projects and client information. Your role is to provide strategic insights, not just data.

*Your Identity:*
• You represent Veza Digital, a premium digital agency
• You serve C-level executives who need strategic insights
• You provide executive-level reports and analysis, not just task lists
• You think like a business consultant, not just a task manager

*Available Tools:*
1. *Client Management*: Search and retrieve client mapping information from Supabase
2. *ClickUp Integration*: Get tasks, create tasks, update tasks, and retrieve project information
3. *Time Tracking*: Analyze hours spent on projects and client work
4. *Employee Management*: Map Slack users to ClickUp users for task assignment

*SUPABASE SCHEMA - ALWAYS USE THESE EXACT FIELD NAMES:*

*client_mappings table fields:*
• client_name (required)
• clickup_project_name
• clickup_folder_name
• clickup_folder_id
• clickup_list_name
• clickup_list_id
• slack_internal_channel_name
• slack_internal_channel_id
• slack_external_channel_name
• slack_external_channel_id
• alternatives (array)
• notes
• qa_list_name
• qa_list_id
• project_type
• available_hours
• revenue
• average_delivery_hourly (NOT average_hourly_rate!)
• status

*employees table fields:*
• real_name
• slack_user_id
• clickup_user_id
• email
• slack_username
• clickup_username
• clickup_role
• clickup_color
• clickup_initials
• is_active

*CRITICAL FIELD MAPPING RULES:*
• When user says "Project Name" → Use clickup_project_name
• When user says "Average Hourly Rate" → Use average_delivery_hourly
• When user says "Folder ID" → Use clickup_folder_id
• When user says "List ID" → Use clickup_list_id
• When user says "Internal Channel" → Use slack_internal_channel_id
• When user says "External Channel" → Use slack_external_channel_id

*Executive-Level Capabilities:*
• Provide strategic project status reports with insights
• Analyze project health and identify risks/opportunities
• Create executive summaries of client work
• Offer business recommendations based on project data
• Track resource allocation and project profitability insights

*Critical Response Guidelines:*
• Always provide insights and analysis, not just raw data
• Think like a business consultant - what does this data mean for the business?
• Identify trends, risks, opportunities, and recommendations
• Present information in executive summary format
• FIRST: Try get_client_by_channel_id with the channel_id from context to find the client
• If channel lookup fails, then extract client names from user queries and use search_client_mappings
• When asked about "what's happening" or "latest updates", use the get_tasks_updated_since tool
• For task creation, always get the client mapping first to find the correct list_id
• When users say "this client" or similar, use the channel_id to identify which client they mean

*MANDATORY SLACK FORMATTING - NO EXCEPTIONS:*
ALL responses MUST use Slack formatting, NOT Markdown. Use ONLY these Slack syntax elements:

*bold text* for emphasis (NEVER use **bold**)
_italic text_ for definitions
~strikethrough~ when needed
`code snippets` for technical terms
• Use manual bullet points (NEVER use - or *)
<URL|text> for links with custom text
>Important callouts and insights

ABSOLUTELY FORBIDDEN: Markdown syntax (**, ##, -, etc.)
MANDATORY: Slack markup only (*text*, _text_, `code`, etc.)

*Executive Response Style:*
• Lead with key insights and business impact
• Provide strategic recommendations
• Use executive summary format
• Include relevant metrics and trends
• Highlight risks and opportunities
• Be concise but comprehensive
• Use emojis strategically (📊 for reports, ⚠️ for risks, 💡 for insights)

Remember: You serve C-level executives who need strategic insights about their client projects, not just task lists. Always provide business value and actionable intelligence."""
    
    def _get_current_datetime_context(self) -> str:
        """
        Generate current date/time context for every prompt.
        This is like n8n's {{ $now }} - always provides current date/time.
        """
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        current_year = now.year
        current_month = now.strftime("%B %Y")  # e.g., "September 2025"
        
        return f"""
*CRITICAL DATE/TIME CONTEXT - ALWAYS USE THESE CURRENT VALUES:*
• RIGHT NOW: {current_datetime}
• TODAY'S DATE: {current_date}
• CURRENT YEAR: {current_year}
• CURRENT MONTH: {current_month}
• WHEN USER SAYS "this month": Use {current_date[:7]} (e.g., 2025-09-01 to 2025-09-30)
• WHEN USER SAYS "this week": Use dates from current week in {current_year}
• WHEN USER SAYS "recent" or "latest": Use {current_year} dates, not 2023!
• FOR TIME TRACKING: Always use {current_year} dates unless user specifies otherwise
• NEVER USE 2023 DATES - WE ARE IN {current_year}!
"""
    
    @property
    def system_prompt(self) -> str:
        """
        Generate the complete system prompt with current date/time context.
        This ensures every GPT-4 call has fresh date/time information.
        """
        datetime_context = self._get_current_datetime_context()
        
        return f"""{self.base_system_prompt}

{datetime_context}"""

    async def process_user_message(
        self, 
        user_message: str, 
        user_id: str = None, 
        channel_id: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Process a user message and return an intelligent response.
        
        This method handles the complete flow from user input to final response,
        including tool calls and conversation management.
        """
        logger.info("Processing user message", 
                   user_message=user_message[:100] + "..." if len(user_message) > 100 else user_message,
                   user_id=user_id, 
                   channel_id=channel_id)
        
        try:
            # Get MCP server and tool schemas
            mcp_server = await get_mcp_server()
            tool_schemas = mcp_server.get_tool_schemas()
            
            # Initialize conversation with FRESH date/time context
            messages = [
                {"role": "system", "content": self.system_prompt},  # This calls the property with fresh date
                {"role": "user", "content": user_message}
            ]
            
            # Add context if provided
            if context:
                context_message = f"Additional context: {json.dumps(context, indent=2)}"
                messages.insert(-1, {"role": "system", "content": context_message})
            
            # Execute conversation loop with tool calls
            final_response = await self._execute_conversation_loop(messages, tool_schemas, mcp_server)
            
            logger.info("Successfully processed user message", 
                       response_length=len(final_response),
                       user_id=user_id)
            
            return final_response
            
        except Exception as e:
            logger.error("Error processing user message", 
                        error=str(e), 
                        user_message=user_message[:100],
                        user_id=user_id)
            return f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."
    
    async def _execute_conversation_loop(
        self, 
        messages: List[Dict[str, Any]], 
        tool_schemas: List[Dict[str, Any]], 
        mcp_server
    ) -> str:
        """
        Execute the conversation loop with tool calls until completion.
        """
        iteration = 0
        last_successful_tools = []
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Conversation iteration {iteration}")
            
            # Call GPT-4 with function calling
            response = await self._call_gpt4_with_tools(messages, tool_schemas)
            
            # Check if GPT-4 wants to call tools
            if response.choices[0].message.tool_calls:
                # Execute tool calls and continue conversation
                messages.append(response.choices[0].message.model_dump())
                
                current_iteration_tools = []
                for tool_call in response.choices[0].message.tool_calls:
                    tool_result = await self._execute_tool_call(tool_call, mcp_server)
                    
                    # Track successful tool calls
                    if not (isinstance(tool_result, dict) and tool_result.get("error")):
                        current_iteration_tools.append({
                            "name": tool_call.function.name,
                            "result": tool_result
                        })
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
                    })
                
                # Update successful tools list
                if current_iteration_tools:
                    last_successful_tools = current_iteration_tools
                
                # Continue the loop to get the final response
                continue
            else:
                # No more tool calls, return the final response
                final_content = response.choices[0].message.content
                if final_content:
                    return final_content
                else:
                    return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
        
        # If we hit max iterations, check if we had successful tool calls
        logger.warning("Hit maximum conversation iterations", max_iterations=self.max_iterations)
        
        # If we had successful tool calls in the last iteration, try to get a final response
        if last_successful_tools:
            logger.info("Attempting final response after successful tool calls", 
                       successful_tools=[tool["name"] for tool in last_successful_tools])
            
            try:
                # Add a system message to force a final response
                final_messages = messages + [{
                    "role": "system", 
                    "content": "You have successfully completed the requested tool calls. Please provide a final response to the user based on the tool results. Do not make any more tool calls."
                }]
                
                # Make one final call to get the response
                final_response = await self._call_gpt4_with_tools(final_messages, [])  # No tools available
                final_content = final_response.choices[0].message.content
                
                if final_content:
                    logger.info("Successfully generated final response after max iterations")
                    return final_content
                    
            except Exception as e:
                logger.error("Failed to generate final response after successful tools", error=str(e))
        
        return "I apologize, but I'm having trouble processing your request completely. Please try breaking it down into smaller questions."
    
    async def _call_gpt4_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tool_schemas: List[Dict[str, Any]]
    ) -> ChatCompletion:
        """Call GPT-4 with function calling enabled."""
        
        # Convert tool schemas to OpenAI format
        tools = []
        for schema in tool_schemas:
            tools.append({
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["parameters"]
                }
            })
        
        logger.debug("Calling GPT-4", 
                    message_count=len(messages),
                    tool_count=len(tools),
                    **log_llm_interaction(self.model))
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=2000
            )
            
            # Log token usage
            if response.usage:
                logger.info("GPT-4 API call completed",
                           **log_llm_interaction(
                               self.model,
                               prompt_tokens=response.usage.prompt_tokens,
                               completion_tokens=response.usage.completion_tokens
                           ))
            
            return response
            
        except Exception as e:
            logger.error("GPT-4 API call failed", error=str(e))
            raise Exception(f"Failed to call GPT-4: {str(e)}")
    
    async def _execute_tool_call(
        self, 
        tool_call: ChatCompletionMessageToolCall, 
        mcp_server
    ) -> Any:
        """Execute a single tool call."""
        
        tool_name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse tool arguments", 
                        tool_name=tool_name, 
                        arguments=tool_call.function.arguments,
                        error=str(e))
            return {"error": f"Invalid tool arguments: {str(e)}"}
        
        logger.info("Executing tool call", tool_name=tool_name, arguments=arguments)
        
        try:
            result = await mcp_server.call_tool(tool_name, arguments)
            logger.debug("Tool call completed successfully", tool_name=tool_name)
            return result
            
        except Exception as e:
            logger.error("Tool call failed", tool_name=tool_name, error=str(e))
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def extract_client_names(self, text: str) -> List[str]:
        """
        Extract potential client names from text using LLM.
        
        This is a helper method for identifying client names in user queries
        when they might not be exact matches.
        """
        logger.debug("Extracting client names from text", text=text[:100])
        
        try:
            # Get all available client names for context
            mcp_server = await get_mcp_server()
            all_clients = await mcp_server.call_tool("get_all_client_names", {})
            
            extraction_prompt = f"""
            Extract any client or company names mentioned in this text: "{text}"
            
            Available clients in the system: {', '.join(all_clients[:20])}  # Show first 20 for context
            
            Return only the client names that are mentioned or closely match the available clients.
            If no clear client names are found, return an empty list.
            
            Respond with a JSON array of client names only, no other text.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            if content:
                try:
                    client_names = json.loads(content)
                    if isinstance(client_names, list):
                        logger.debug("Extracted client names", client_names=client_names)
                        return client_names
                except json.JSONDecodeError:
                    pass
            
            return []
            
        except Exception as e:
            logger.error("Error extracting client names", error=str(e))
            return []
    
    async def close(self):
        """Clean up resources."""
        logger.info("Closing LLM orchestrator")
        await self.client.close()


# Global orchestrator instance
llm_orchestrator = LLMOrchestrator()


async def get_llm_orchestrator() -> LLMOrchestrator:
    """Get the global LLM orchestrator instance."""
    return llm_orchestrator
