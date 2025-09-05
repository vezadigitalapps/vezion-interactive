"""
MCP-Style Server Implementation for Slack Bot.

This module implements an MCP-style server that exposes all tools to the 
LLM orchestrator using standardized tool interfaces (without external MCP dependency).
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
import json
import inspect
from datetime import datetime

from .tools import (
    # Supabase tools
    get_client_mapping,
    search_client_mappings,
    get_all_client_names,
    update_client_mapping,
    create_client_mapping,
    get_client_by_channel_id,
    get_employee_by_slack_id,
    get_all_employees,
    
    # ClickUp tools
    get_tasks_by_list_id,
    get_tasks_updated_since,
    create_task,
    update_task,
    get_task_details,
    get_list_details,
    get_tasks_with_time_spent,
)

from .utils import get_logger, log_mcp_tool_call

logger = get_logger(__name__)


class ToolDefinition:
    """Simple tool definition class."""
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description


class SlackBotMCPServer:
    """MCP-Style Server for the Slack Bot with all registered tools."""
    
    def __init__(self):
        self.tools: List[ToolDefinition] = []
        self._register_tools()
        logger.info("MCP-Style Server initialized with tools")
    
    def _register_tools(self):
        """Register all tools with the server."""
        
        # Supabase Tools
        async def get_client_mapping_tool(client_name: str) -> Dict[str, Any]:
            """
            Retrieve client mapping information by name from Supabase.
            
            This tool searches for a client by name and returns their complete
            mapping information including ClickUp IDs and Slack channel details.
            Use this when you need to find ClickUp list IDs or other client details.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_client_mapping", {"client_name": client_name}))
            return await get_client_mapping(client_name)
        
        async def search_client_mappings_tool(query: str) -> List[Dict[str, Any]]:
            """
            Search for client mappings using a flexible query.
            
            This tool performs a fuzzy search across client names and alternatives
            to help identify the correct client when the exact name isn't known.
            Use this when the user mentions a client name that might not be exact.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("search_client_mappings", {"query": query}))
            return await search_client_mappings(query)
        
        async def get_all_client_names_tool() -> List[str]:
            """
            Get a list of all client names for reference.
            
            This tool returns all available client names to help with
            client name extraction and validation. Use this to understand
            what clients are available in the system.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_all_client_names", {}))
            return await get_all_client_names()
        
        async def update_client_mapping_tool(client_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            """
            Update client mapping information in Supabase.
            
            This tool allows updating specific fields of a client mapping record.
            Use with caution as it modifies the database. Only use when explicitly
            requested by the user to update client information.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("update_client_mapping", {"client_name": client_name, "updates": updates}))
            return await update_client_mapping(client_name, updates)
        
        async def create_client_mapping_tool(mapping_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Create a new client mapping in Supabase.
            
            This tool creates a new client mapping record with the provided data.
            Use when adding a new client to the system. Requires at minimum
            a client_name field.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("create_client_mapping", {"mapping_data": mapping_data}))
            return await create_client_mapping(mapping_data)
        
        async def get_client_by_channel_id_tool(channel_id: str) -> Dict[str, Any]:
            """
            Get client mapping by Slack channel ID.
            
            This tool searches for a client using the Slack channel ID,
            which is useful when the bot is mentioned in a specific client channel.
            Use this first when you know the channel ID to find the correct client.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_client_by_channel_id", {"channel_id": channel_id}))
            return await get_client_by_channel_id(channel_id)
        
        # ClickUp Tools
        async def get_tasks_by_list_id_tool(
            list_id: str,
            archived: Optional[bool] = None,
            include_closed: Optional[bool] = None,
            subtasks: Optional[bool] = None,
            statuses: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None,
            due_date_gt: Optional[int] = None,
            due_date_lt: Optional[int] = None,
            date_created_gt: Optional[int] = None,
            date_created_lt: Optional[int] = None,
            date_updated_gt: Optional[int] = None,
            date_updated_lt: Optional[int] = None,
            page: Optional[int] = None,
            order_by: Optional[str] = None,
            reverse: Optional[bool] = None
        ) -> List[Dict[str, Any]]:
            """
            Get tasks from a specific ClickUp list by ID.
            
            This tool retrieves tasks from a ClickUp list using the list ID,
            with optional filtering for status, date ranges, etc. Use this
            after getting the list_id from client mapping to fetch tasks.
            
            Date filters expect Unix timestamps in milliseconds.
            """
            filters = {k: v for k, v in locals().items() if k != 'list_id' and v is not None}
            logger.info("MCP tool called", **log_mcp_tool_call("get_tasks_by_list_id", {"list_id": list_id, "filters": filters}))
            return await get_tasks_by_list_id(list_id, **filters)
        
        async def get_tasks_updated_since_tool(list_id: str, hours_ago: int = 24) -> List[Dict[str, Any]]:
            """
            Get tasks updated within the specified time period.
            
            This tool retrieves tasks that have been updated within the last N hours,
            useful for getting recent activity on a client's project. Perfect for
            answering "what's been happening with Client X this week" type questions.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_tasks_updated_since", {"list_id": list_id, "hours_ago": hours_ago}))
            return await get_tasks_updated_since(list_id, hours_ago)
        
        async def create_task_tool(list_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Create a new task in a ClickUp list.
            
            This tool creates a task with the specified data in the given list.
            Required: name field in task_data.
            Optional: description, markdown_description, status, priority, due_date, assignees.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("create_task", {"list_id": list_id, "task_data": task_data}))
            return await create_task(list_id, task_data)
        
        async def update_task_tool(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            """
            Update an existing ClickUp task.
            
            This tool updates specific fields of a task. Only the fields
            provided in updates will be modified.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("update_task", {"task_id": task_id, "updates": updates}))
            return await update_task(task_id, updates)
        
        async def get_task_details_tool(task_id: str) -> Dict[str, Any]:
            """
            Get detailed information about a specific task.
            
            This tool retrieves comprehensive task details including custom fields,
            comments, and other metadata. Use when you need full task information.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_task_details", {"task_id": task_id}))
            return await get_task_details(task_id)
        
        async def get_list_details_tool(list_id: str) -> Dict[str, Any]:
            """
            Get details about a ClickUp list.
            
            This tool retrieves list information including available statuses.
            Useful for understanding what statuses are available when creating/updating tasks.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_list_details", {"list_id": list_id}))
            return await get_list_details(list_id)
        
        async def get_tasks_with_time_spent_tool(list_id: str, **filters) -> Dict[str, Any]:
            """
            Get tasks with time spent information from task details.
            
            This tool retrieves tasks and calculates total time spent from task details
            instead of using the buggy time entries API. Perfect for answering
            questions about project hours and time allocation.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_tasks_with_time_spent", {"list_id": list_id, "filters": filters}))
            return await get_tasks_with_time_spent(list_id, **filters)
        
        async def get_employee_by_slack_id_tool(slack_user_id: str) -> Dict[str, Any]:
            """
            Get employee mapping by Slack user ID.
            
            This tool finds the ClickUp user ID for a Slack user to enable task assignments.
            Use this when you need to assign tasks to users mentioned in Slack.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_employee_by_slack_id", {"slack_user_id": slack_user_id}))
            return await get_employee_by_slack_id(slack_user_id)
        
        async def get_all_employees_tool() -> List[Dict[str, Any]]:
            """
            Get all employees for reference.
            
            This tool returns all employee mappings to help with user assignment
            and understanding who can be assigned to tasks.
            """
            logger.info("MCP tool called", **log_mcp_tool_call("get_all_employees", {}))
            return await get_all_employees()
        
        # Register all tools
        self.tools = [
            ToolDefinition("get_client_mapping", get_client_mapping_tool, get_client_mapping_tool.__doc__),
            ToolDefinition("search_client_mappings", search_client_mappings_tool, search_client_mappings_tool.__doc__),
            ToolDefinition("get_all_client_names", get_all_client_names_tool, get_all_client_names_tool.__doc__),
            ToolDefinition("update_client_mapping", update_client_mapping_tool, update_client_mapping_tool.__doc__),
            ToolDefinition("create_client_mapping", create_client_mapping_tool, create_client_mapping_tool.__doc__),
            ToolDefinition("get_client_by_channel_id", get_client_by_channel_id_tool, get_client_by_channel_id_tool.__doc__),
            ToolDefinition("get_employee_by_slack_id", get_employee_by_slack_id_tool, get_employee_by_slack_id_tool.__doc__),
            ToolDefinition("get_all_employees", get_all_employees_tool, get_all_employees_tool.__doc__),
            ToolDefinition("get_tasks_by_list_id", get_tasks_by_list_id_tool, get_tasks_by_list_id_tool.__doc__),
            ToolDefinition("get_tasks_updated_since", get_tasks_updated_since_tool, get_tasks_updated_since_tool.__doc__),
            ToolDefinition("create_task", create_task_tool, create_task_tool.__doc__),
            ToolDefinition("update_task", update_task_tool, update_task_tool.__doc__),
            ToolDefinition("get_task_details", get_task_details_tool, get_task_details_tool.__doc__),
            ToolDefinition("get_list_details", get_list_details_tool, get_list_details_tool.__doc__),
            ToolDefinition("get_tasks_with_time_spent", get_tasks_with_time_spent_tool, get_tasks_with_time_spent_tool.__doc__),
        ]
        
        logger.info("All MCP tools registered successfully", tool_count=len(self.tools))
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool by name with the given arguments.
        
        This method provides a programmatic way to call tools from the LLM orchestrator.
        """
        logger.debug("Calling MCP tool", tool_name=tool_name, arguments=arguments)
        
        try:
            # Find the tool function
            tool_func = None
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_func = tool.func
                    break
            
            if not tool_func:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            # Call the tool function
            result = await tool_func(**arguments)
            
            logger.debug("MCP tool completed successfully", tool_name=tool_name)
            return result
            
        except Exception as e:
            logger.error("MCP tool call failed", tool_name=tool_name, error=str(e))
            raise Exception(f"Tool call failed: {str(e)}")
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get the JSON schemas for all registered tools.
        
        This is used by the LLM orchestrator to understand what tools are available
        and how to call them.
        """
        schemas = []
        
        for tool in self.tools:
            # Get function signature
            sig = inspect.signature(tool.func)
            
            # Build parameter schema
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                param_type = param.annotation
                param_schema = self._get_type_schema(param_type)
                
                properties[param_name] = param_schema
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            schema = {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
            schemas.append(schema)
        
        return schemas
    
    def _get_type_schema(self, param_type) -> Dict[str, Any]:
        """Convert Python type annotations to JSON schema."""
        if param_type == str:
            return {"type": "string"}
        elif param_type == int:
            return {"type": "integer"}
        elif param_type == float:
            return {"type": "number"}
        elif param_type == bool:
            return {"type": "boolean"}
        elif hasattr(param_type, '__origin__'):
            if param_type.__origin__ == list:
                item_type = param_type.__args__[0] if param_type.__args__ else str
                return {
                    "type": "array",
                    "items": self._get_type_schema(item_type)
                }
            elif param_type.__origin__ == dict:
                return {"type": "object"}
            elif param_type.__origin__ == Union:
                # Handle Optional types (Union[X, None])
                non_none_types = [t for t in param_type.__args__ if t != type(None)]
                if len(non_none_types) == 1:
                    return self._get_type_schema(non_none_types[0])
        
        # Default to string for unknown types
        return {"type": "string"}
    
    async def close(self):
        """Clean up resources."""
        logger.info("Closing MCP server")
        # Close any tool connections
        from .tools import clickup_tools
        await clickup_tools.close()


# Global MCP server instance
mcp_server = SlackBotMCPServer()


async def get_mcp_server() -> SlackBotMCPServer:
    """Get the global MCP server instance."""
    return mcp_server
