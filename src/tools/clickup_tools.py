"""
ClickUp MCP Tools for Task Management Operations.

This module provides MCP-compliant tools for interacting with ClickUp API,
enabling targeted task operations without fetching entire workspace hierarchy.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import httpx
from pydantic import BaseModel, Field

from ..utils import get_logger, log_function_call, log_api_call, get_config

logger = get_logger(__name__)
config = get_config()


class ClickUpTask(BaseModel):
    """ClickUp task data model."""
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[Dict[str, Any]] = None
    priority: Optional[Dict[str, Any]] = None
    due_date: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    assignees: Optional[List[Dict[str, Any]]] = None
    list: Optional[Dict[str, Any]] = None
    url: Optional[str] = None


class ClickUpTools:
    """ClickUp tools for task management operations."""
    
    def __init__(self):
        self.api_token = config.clickup_api_token
        self.team_id = config.clickup_team_id
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0
            )
        return self._client
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to ClickUp API."""
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        
        logger.debug("Making ClickUp API request", **log_api_call("clickup", endpoint, method))
        
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("ClickUp API error", status_code=e.response.status_code, response=e.response.text)
            raise Exception(f"ClickUp API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error("Request failed", error=str(e))
            raise Exception(f"Request failed: {str(e)}")
    
    async def get_tasks_by_list_id(self, list_id: str, **filters) -> List[Dict[str, Any]]:
        """
        Get tasks from a specific ClickUp list by ID.
        
        This tool retrieves tasks from a ClickUp list using the list ID,
        with optional filtering for status, date ranges, etc.
        """
        logger.info("Getting tasks by list ID", **log_function_call("get_tasks_by_list_id", list_id=list_id, filters=filters))
        
        try:
            # Build query parameters
            params = {}
            
            # Add common filters
            if filters.get("archived"):
                params["archived"] = "true"
            if filters.get("include_closed"):
                params["include_closed"] = "true"
            if filters.get("subtasks"):
                params["subtasks"] = "true"
            if filters.get("statuses"):
                params["statuses[]"] = filters["statuses"]
            if filters.get("assignees"):
                params["assignees[]"] = filters["assignees"]
            
            # Date filters (expecting Unix timestamps in milliseconds)
            date_filters = ["due_date_gt", "due_date_lt", "date_created_gt", "date_created_lt", "date_updated_gt", "date_updated_lt"]
            for filter_name in date_filters:
                if filters.get(filter_name):
                    params[filter_name] = filters[filter_name]
            
            # Pagination
            if filters.get("page"):
                params["page"] = filters["page"]
            
            # Ordering
            if filters.get("order_by"):
                params["order_by"] = filters["order_by"]
            if filters.get("reverse"):
                params["reverse"] = "true"
            
            response = await self._make_request("GET", f"/list/{list_id}/task", params=params)
            
            tasks = response.get("tasks", [])
            logger.info("Successfully retrieved tasks", list_id=list_id, task_count=len(tasks))
            
            return tasks
            
        except Exception as e:
            logger.error("Error retrieving tasks", list_id=list_id, error=str(e))
            raise Exception(f"Failed to retrieve tasks from list {list_id}: {str(e)}")
    
    async def get_tasks_updated_since(self, list_id: str, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Get tasks updated within the specified time period.
        
        This tool retrieves tasks that have been updated within the last N hours,
        useful for getting recent activity on a client's project.
        """
        logger.info("Getting recently updated tasks", **log_function_call("get_tasks_updated_since", list_id=list_id, hours_ago=hours_ago))
        
        try:
            # Calculate timestamp for N hours ago (ClickUp expects milliseconds)
            cutoff_time = datetime.now() - timedelta(hours=hours_ago)
            timestamp_ms = int(cutoff_time.timestamp() * 1000)
            
            tasks = await self.get_tasks_by_list_id(
                list_id,
                date_updated_gt=timestamp_ms,
                include_closed=True,
                subtasks=True
            )
            
            logger.info("Successfully retrieved updated tasks", list_id=list_id, task_count=len(tasks), hours_ago=hours_ago)
            return tasks
            
        except Exception as e:
            logger.error("Error retrieving updated tasks", list_id=list_id, hours_ago=hours_ago, error=str(e))
            raise Exception(f"Failed to retrieve updated tasks: {str(e)}")
    
    async def create_task(self, list_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task in a ClickUp list.
        
        This tool creates a task with the specified data in the given list.
        """
        logger.info("Creating task", **log_function_call("create_task", list_id=list_id, task_name=task_data.get("name")))
        
        try:
            # Prepare task payload
            payload = {
                "name": task_data["name"],
                "description": task_data.get("description", ""),
                "markdown_description": task_data.get("markdown_description"),
                "status": task_data.get("status"),
                "due_date": task_data.get("due_date"),
                "assignees": task_data.get("assignees", [])
            }
            
            # Handle priority conversion (ClickUp expects 1-4, not strings)
            if task_data.get("priority"):
                priority_map = {
                    "urgent": 1,
                    "high": 2, 
                    "normal": 3,
                    "low": 4,
                    1: 1, 2: 2, 3: 3, 4: 4  # Allow direct numbers too
                }
                priority_value = task_data.get("priority")
                if isinstance(priority_value, str):
                    priority_value = priority_value.lower()
                
                if priority_value in priority_map:
                    payload["priority"] = priority_map[priority_value]
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = await self._make_request("POST", f"/list/{list_id}/task", json=payload)
            
            task = response
            logger.info("Successfully created task", list_id=list_id, task_id=task.get("id"), task_name=task.get("name"))
            
            return task
            
        except Exception as e:
            logger.error("Error creating task", list_id=list_id, task_name=task_data.get("name"), error=str(e))
            raise Exception(f"Failed to create task: {str(e)}")
    
    async def get_team_members(self) -> List[Dict[str, Any]]:
        """
        Get team members from ClickUp workspace.
        
        This tool retrieves all team members to help with user ID mapping
        for task assignments.
        """
        logger.info("Getting team members", **log_function_call("get_team_members"))
        
        try:
            response = await self._make_request("GET", f"/team/{self.team_id}")
            
            members = response.get("team", {}).get("members", [])
            logger.info("Successfully retrieved team members", member_count=len(members))
            
            return members
            
        except Exception as e:
            logger.error("Error retrieving team members", error=str(e))
            raise Exception(f"Failed to retrieve team members: {str(e)}")
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing ClickUp task.
        
        This tool updates specific fields of a task.
        """
        logger.info("Updating task", **log_function_call("update_task", task_id=task_id, updates=updates))
        
        try:
            # Prepare update payload
            payload = {}
            
            if "name" in updates:
                payload["name"] = updates["name"]
            if "description" in updates:
                payload["description"] = updates["description"]
            if "markdown_description" in updates:
                payload["markdown_description"] = updates["markdown_description"]
            if "status" in updates:
                payload["status"] = updates["status"]
            if "priority" in updates:
                payload["priority"] = updates["priority"]
            if "due_date" in updates:
                payload["due_date"] = updates["due_date"]
            if "assignees" in updates:
                payload["assignees"] = {"add": updates["assignees"]}
            
            response = await self._make_request("PUT", f"/task/{task_id}", json=payload)
            
            logger.info("Successfully updated task", task_id=task_id)
            return response
            
        except Exception as e:
            logger.error("Error updating task", task_id=task_id, error=str(e))
            raise Exception(f"Failed to update task {task_id}: {str(e)}")
    
    async def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific task.
        
        This tool retrieves comprehensive task details including custom fields,
        comments, and other metadata.
        """
        logger.info("Getting task details", **log_function_call("get_task_details", task_id=task_id))
        
        try:
            response = await self._make_request("GET", f"/task/{task_id}")
            
            logger.info("Successfully retrieved task details", task_id=task_id, task_name=response.get("name"))
            return response
            
        except Exception as e:
            logger.error("Error retrieving task details", task_id=task_id, error=str(e))
            raise Exception(f"Failed to retrieve task details for {task_id}: {str(e)}")
    
    async def get_list_details(self, list_id: str) -> Dict[str, Any]:
        """
        Get details about a ClickUp list.
        
        This tool retrieves list information including available statuses.
        """
        logger.info("Getting list details", **log_function_call("get_list_details", list_id=list_id))
        
        try:
            response = await self._make_request("GET", f"/list/{list_id}")
            
            logger.info("Successfully retrieved list details", list_id=list_id, list_name=response.get("name"))
            return response
            
        except Exception as e:
            logger.error("Error retrieving list details", list_id=list_id, error=str(e))
            raise Exception(f"Failed to retrieve list details for {list_id}: {str(e)}")
    
    async def get_tasks_with_time_spent(self, list_id: str, **filters) -> Dict[str, Any]:
        """
        Get tasks with time spent information from task details.
        
        This tool retrieves tasks and calculates total time spent from task details
        instead of using the buggy time entries API.
        """
        logger.info("Getting tasks with time spent", **log_function_call("get_tasks_with_time_spent", list_id=list_id, filters=filters))
        
        try:
            # Get all tasks from the list
            tasks = await self.get_tasks_by_list_id(list_id, **filters)
            
            total_time_spent = 0
            tasks_with_time = []
            
            for task in tasks:
                time_spent = task.get("time_spent", 0)  # Time in milliseconds
                if time_spent:
                    # Convert milliseconds to hours
                    hours_spent = time_spent / (1000 * 60 * 60)
                    total_time_spent += hours_spent
                    
                    tasks_with_time.append({
                        "id": task.get("id"),
                        "name": task.get("name"),
                        "status": task.get("status", {}).get("status"),
                        "time_spent_ms": time_spent,
                        "time_spent_hours": round(hours_spent, 2),
                        "assignees": task.get("assignees", []),
                        "url": task.get("url")
                    })
            
            result = {
                "tasks": tasks_with_time,
                "total_tasks": len(tasks),
                "tasks_with_time": len(tasks_with_time),
                "total_hours_spent": round(total_time_spent, 2)
            }
            
            logger.info("Successfully calculated time spent from tasks", 
                       list_id=list_id, 
                       total_tasks=len(tasks),
                       total_hours=round(total_time_spent, 2))
            
            return result
            
        except Exception as e:
            logger.error("Error getting tasks with time spent", list_id=list_id, error=str(e))
            raise Exception(f"Failed to get tasks with time spent: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instance
clickup_tools = ClickUpTools()


# MCP Tool Functions (these will be registered with the MCP server)
async def get_tasks_by_list_id(list_id: str, **filters) -> List[Dict[str, Any]]:
    """MCP tool: Get tasks from a ClickUp list."""
    return await clickup_tools.get_tasks_by_list_id(list_id, **filters)


async def get_tasks_updated_since(list_id: str, hours_ago: int = 24) -> List[Dict[str, Any]]:
    """MCP tool: Get recently updated tasks."""
    return await clickup_tools.get_tasks_updated_since(list_id, hours_ago)


async def create_task(list_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool: Create a new task."""
    return await clickup_tools.create_task(list_id, task_data)


async def update_task(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool: Update an existing task."""
    return await clickup_tools.update_task(task_id, updates)


async def get_task_details(task_id: str) -> Dict[str, Any]:
    """MCP tool: Get detailed task information."""
    return await clickup_tools.get_task_details(task_id)


async def get_list_details(list_id: str) -> Dict[str, Any]:
    """MCP tool: Get list information."""
    return await clickup_tools.get_list_details(list_id)


async def get_tasks_with_time_spent(list_id: str, **filters) -> Dict[str, Any]:
    """MCP tool: Get tasks with time spent from task details."""
    return await clickup_tools.get_tasks_with_time_spent(list_id, **filters)
