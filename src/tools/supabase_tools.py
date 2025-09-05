"""
Supabase MCP Tools for Client Mapping Operations.

This module provides MCP-compliant tools for interacting with the Supabase
client mapping database, enabling the bot to retrieve and manage client
information efficiently.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from supabase import create_client, Client
from pydantic import BaseModel, Field

from ..utils import get_logger, log_function_call, log_api_call, get_config

logger = get_logger(__name__)
config = get_config()


class ClientMapping(BaseModel):
    """Client mapping data model matching the Supabase schema."""
    id: Optional[str] = None
    client_name: str
    clickup_project_name: Optional[str] = None
    clickup_folder_name: Optional[str] = None
    clickup_folder_id: Optional[str] = None
    clickup_list_name: Optional[str] = None
    clickup_list_id: Optional[str] = None
    slack_internal_channel_name: Optional[str] = None
    slack_internal_channel_id: Optional[str] = None
    slack_external_channel_name: Optional[str] = None
    slack_external_channel_id: Optional[str] = None
    alternatives: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    qa_list_name: Optional[str] = None
    qa_list_id: Optional[str] = None
    project_type: Optional[str] = None
    available_hours: Optional[str] = None
    revenue: Optional[float] = None
    average_delivery_hourly: Optional[float] = None
    status: Optional[str] = None


class SupabaseTools:
    """Supabase tools for client mapping operations."""
    
    def __init__(self):
        self.client: Client = create_client(
            config.supabase_url,
            config.supabase_service_key
        )
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL."""
        if not self._cache_timestamp:
            return False
        
        cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
        return cache_age < config.cache_ttl_seconds
    
    async def get_client_mapping(self, client_name: str) -> Dict[str, Any]:
        """
        Retrieve client mapping information by name from Supabase.
        
        This tool searches for a client by name and returns their complete
        mapping information including ClickUp IDs and Slack channel details.
        """
        logger.info("Getting client mapping", **log_function_call("get_client_mapping", client_name=client_name))
        
        try:
            # Check cache first
            cache_key = f"client_mapping_{client_name.lower()}"
            if self._is_cache_valid() and cache_key in self._cache:
                logger.debug("Returning cached client mapping", client_name=client_name)
                return self._cache[cache_key]
            
            # Query Supabase
            logger.debug("Querying Supabase for client mapping", **log_api_call("supabase", "client_mappings", "SELECT"))
            
            # Search by exact name first
            response = self.client.table("client_mappings").select("*").eq("client_name", client_name).execute()
            
            if not response.data:
                # Try case-insensitive search
                response = self.client.table("client_mappings").select("*").ilike("client_name", f"%{client_name}%").execute()
            
            if not response.data:
                # Try searching in alternatives
                response = self.client.table("client_mappings").select("*").contains("alternatives", [client_name]).execute()
            
            if response.data:
                result = response.data[0]  # Take the first match
                
                # Cache the result
                self._cache[cache_key] = result
                self._cache_timestamp = datetime.now()
                
                logger.info("Successfully retrieved client mapping", client_name=client_name, found_id=result.get("id"))
                return result
            else:
                logger.warning("Client mapping not found", client_name=client_name)
                return {}
                
        except Exception as e:
            logger.error("Error retrieving client mapping", client_name=client_name, error=str(e))
            raise Exception(f"Failed to retrieve client mapping for {client_name}: {str(e)}")
    
    async def search_client_mappings(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for client mappings using a flexible query.
        
        This tool performs a fuzzy search across client names, channel names, and alternatives
        to help identify the correct client when the exact name isn't known.
        """
        logger.info("Searching client mappings", **log_function_call("search_client_mappings", query=query))
        
        try:
            # Enhanced search across multiple fields including channel names
            response = self.client.table("client_mappings").select("*").or_(
                f"client_name.ilike.%{query}%,"
                f"clickup_project_name.ilike.%{query}%,"
                f"slack_internal_channel_name.ilike.%{query}%,"
                f"slack_external_channel_name.ilike.%{query}%,"
                f"alternatives.cs.{{{query}}}"
            ).execute()
            
            results = response.data or []
            logger.info("Search completed", query=query, results_count=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Error searching client mappings", query=query, error=str(e))
            raise Exception(f"Failed to search client mappings: {str(e)}")
    
    async def get_client_by_channel_id(self, channel_id: str) -> Dict[str, Any]:
        """
        Get client mapping by Slack channel ID.
        
        This tool searches for a client using the Slack channel ID,
        which is useful when the bot is mentioned in a specific client channel.
        """
        logger.info("Getting client by channel ID", **log_function_call("get_client_by_channel_id", channel_id=channel_id))
        
        try:
            # Search by internal or external channel ID
            response = self.client.table("client_mappings").select("*").or_(
                f"slack_internal_channel_id.eq.{channel_id},"
                f"slack_external_channel_id.eq.{channel_id}"
            ).execute()
            
            if response.data:
                result = response.data[0]  # Take the first match
                logger.info("Successfully found client by channel ID", channel_id=channel_id, client_name=result.get("client_name"))
                return result
            else:
                logger.warning("No client found for channel ID", channel_id=channel_id)
                return {}
                
        except Exception as e:
            logger.error("Error getting client by channel ID", channel_id=channel_id, error=str(e))
            raise Exception(f"Failed to get client by channel ID {channel_id}: {str(e)}")
    
    async def get_all_client_names(self) -> List[str]:
        """
        Get a list of all client names for reference.
        
        This tool returns all available client names to help with
        client name extraction and validation.
        """
        logger.info("Getting all client names", **log_function_call("get_all_client_names"))
        
        try:
            # Check cache first
            cache_key = "all_client_names"
            if self._is_cache_valid() and cache_key in self._cache:
                logger.debug("Returning cached client names")
                return self._cache[cache_key]
            
            response = self.client.table("client_mappings").select("client_name, alternatives").execute()
            
            client_names = set()
            for row in response.data or []:
                client_names.add(row["client_name"])
                if row.get("alternatives"):
                    client_names.update(row["alternatives"])
            
            result = sorted(list(client_names))
            
            # Cache the result
            self._cache[cache_key] = result
            self._cache_timestamp = datetime.now()
            
            logger.info("Retrieved all client names", count=len(result))
            return result
            
        except Exception as e:
            logger.error("Error retrieving client names", error=str(e))
            raise Exception(f"Failed to retrieve client names: {str(e)}")
    
    async def update_client_mapping(self, client_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update client mapping information in Supabase.
        
        This tool allows updating specific fields of a client mapping record.
        Use with caution as it modifies the database.
        """
        logger.info("Updating client mapping", **log_function_call("update_client_mapping", client_name=client_name, updates=updates))
        
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            response = self.client.table("client_mappings").update(updates).eq("client_name", client_name).execute()
            
            if response.data:
                result = response.data[0]
                
                # Invalidate cache
                self._cache.clear()
                self._cache_timestamp = None
                
                logger.info("Successfully updated client mapping", client_name=client_name, updated_id=result.get("id"))
                return result
            else:
                logger.warning("No client mapping found to update", client_name=client_name)
                return {}
                
        except Exception as e:
            logger.error("Error updating client mapping", client_name=client_name, error=str(e))
            raise Exception(f"Failed to update client mapping for {client_name}: {str(e)}")
    
    async def create_client_mapping(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new client mapping in Supabase.
        
        This tool creates a new client mapping record with the provided data.
        Use when adding a new client to the system.
        """
        logger.info("Creating client mapping", **log_function_call("create_client_mapping", client_name=mapping_data.get("client_name")))
        
        try:
            # Add timestamps
            now = datetime.now().isoformat()
            mapping_data["created_at"] = now
            mapping_data["updated_at"] = now
            
            response = self.client.table("client_mappings").insert(mapping_data).execute()
            
            if response.data:
                result = response.data[0]
                
                # Invalidate cache
                self._cache.clear()
                self._cache_timestamp = None
                
                logger.info("Successfully created client mapping", client_name=mapping_data.get("client_name"), created_id=result.get("id"))
                return result
            else:
                logger.error("Failed to create client mapping - no data returned")
                return {}
                
        except Exception as e:
            logger.error("Error creating client mapping", client_name=mapping_data.get("client_name"), error=str(e))
            raise Exception(f"Failed to create client mapping: {str(e)}")
    
    async def get_employee_by_slack_id(self, slack_user_id: str) -> Dict[str, Any]:
        """
        Get employee mapping by Slack user ID.
        
        This tool finds the ClickUp user ID for a Slack user to enable task assignments.
        """
        logger.info("Getting employee by Slack ID", **log_function_call("get_employee_by_slack_id", slack_user_id=slack_user_id))
        
        try:
            response = self.client.table("employees").select("*").eq("slack_user_id", slack_user_id).execute()
            
            if response.data:
                result = response.data[0]
                logger.info("Successfully found employee", slack_user_id=slack_user_id, clickup_user_id=result.get("clickup_user_id"))
                return result
            else:
                logger.warning("No employee found for Slack user ID", slack_user_id=slack_user_id)
                return {}
                
        except Exception as e:
            logger.error("Error getting employee by Slack ID", slack_user_id=slack_user_id, error=str(e))
            raise Exception(f"Failed to get employee by Slack ID {slack_user_id}: {str(e)}")
    
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        Get all employees for reference.
        
        This tool returns all employee mappings to help with user assignment.
        """
        logger.info("Getting all employees", **log_function_call("get_all_employees"))
        
        try:
            response = self.client.table("employees").select("*").eq("is_active", True).execute()
            
            employees = response.data or []
            logger.info("Retrieved all employees", count=len(employees))
            return employees
            
        except Exception as e:
            logger.error("Error retrieving employees", error=str(e))
            raise Exception(f"Failed to retrieve employees: {str(e)}")


# Global instance
supabase_tools = SupabaseTools()


# MCP Tool Functions (these will be registered with the MCP server)
async def get_client_mapping(client_name: str) -> Dict[str, Any]:
    """MCP tool: Get client mapping by name."""
    return await supabase_tools.get_client_mapping(client_name)


async def search_client_mappings(query: str) -> List[Dict[str, Any]]:
    """MCP tool: Search client mappings."""
    return await supabase_tools.search_client_mappings(query)


async def get_all_client_names() -> List[str]:
    """MCP tool: Get all client names."""
    return await supabase_tools.get_all_client_names()


async def update_client_mapping(client_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool: Update client mapping."""
    return await supabase_tools.update_client_mapping(client_name, updates)


async def create_client_mapping(mapping_data: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool: Create new client mapping."""
    return await supabase_tools.create_client_mapping(mapping_data)


async def get_client_by_channel_id(channel_id: str) -> Dict[str, Any]:
    """MCP tool: Get client mapping by Slack channel ID."""
    return await supabase_tools.get_client_by_channel_id(channel_id)


async def get_employee_by_slack_id(slack_user_id: str) -> Dict[str, Any]:
    """MCP tool: Get employee mapping by Slack user ID."""
    return await supabase_tools.get_employee_by_slack_id(slack_user_id)


async def get_all_employees() -> List[Dict[str, Any]]:
    """MCP tool: Get all employees."""
    return await supabase_tools.get_all_employees()
