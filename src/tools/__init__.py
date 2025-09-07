"""
MCP Tools for the Slack Bot.

This module provides all the tools that will be registered with the MCP server
for use by the LLM orchestrator.
"""

from .supabase_tools import (
    get_client_mapping,
    search_client_mappings,
    get_all_client_names,
    update_client_mapping,
    create_client_mapping,
    get_client_by_channel_id,
    get_employee_by_slack_id,
    get_all_employees,
    supabase_tools
)

from .clickup_tools import (
    get_tasks_by_list_id,
    get_tasks_updated_since,
    create_task,
    update_task,
    get_task_details,
    get_list_details,
    get_tasks_with_time_spent,
    create_time_entry,
    get_task_time_tracking,
    clickup_tools
)

__all__ = [
    # Supabase tools
    "get_client_mapping",
    "search_client_mappings", 
    "get_all_client_names",
    "update_client_mapping",
    "create_client_mapping",
    "get_client_by_channel_id",
    "get_employee_by_slack_id",
    "get_all_employees",
    "supabase_tools",
    
    # ClickUp tools
    "get_tasks_by_list_id",
    "get_tasks_updated_since",
    "create_task",
    "update_task",
    "get_task_details",
    "get_list_details",
    "get_tasks_with_time_spent",
    "create_time_entry",
    "get_task_time_tracking",
    "clickup_tools",
]
