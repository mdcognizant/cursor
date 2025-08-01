"""Python SDK for LLM Agent Bridge REST API."""

import logging
from typing import Dict, List, Optional, Any, AsyncIterator, Iterator
from urllib.parse import urljoin
import json

import httpx
import asyncio
from contextlib import asynccontextmanager

from .api.models import (
    SendMessageRequest, SendMessageResponse, Message, MessageOptions,
    Agent, CreateAgentRequest, UpdateAgentRequest,
    Task, ExecuteTaskRequest, TaskUpdate,
    ListAgentsRequest, ListAgentsResponse,
    HealthStatus, SchemaListResponse
)
from .exceptions import BridgeError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


class AgentSDK:
    """Python SDK for interacting with the LLM Agent Bridge API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True
    ):
        """Initialize the Agent SDK.
        
        Args:
            base_url: Base URL of the Agent Bridge API
            api_key: API key for authentication
            jwt_token: JWT token for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Setup headers
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LLM-Agent-Bridge-SDK/0.1.0"
        }
        
        # Add authentication headers
        if jwt_token:
            self.headers["Authorization"] = f"Bearer {jwt_token}"
        elif api_key:
            self.headers["X-API-Key"] = api_key
        
        # Create HTTP client
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            verify=verify_ssl
        )
        
        # Create async HTTP client
        self.async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            verify=verify_ssl
        )
        
        logger.info(f"AgentSDK initialized for {self.base_url}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
    
    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
    
    async def aclose(self) -> None:
        """Close the async HTTP client."""
        await self.async_client.aclose()
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and extract data."""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except json.JSONDecodeError:
            raise BridgeError(f"Invalid JSON response: {response.text}")
    
    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and convert to appropriate exceptions."""
        status_code = error.response.status_code
        
        try:
            error_data = error.response.json()
            error_info = error_data.get("error", {})
            message = error_info.get("message", str(error))
            code = error_info.get("code", f"HTTP_{status_code}")
        except:
            message = str(error)
            code = f"HTTP_{status_code}"
        
        if status_code == 401:
            raise AuthenticationError(message)
        elif status_code == 422:
            raise ValidationError(message)
        else:
            raise BridgeError(message, code=code)
    
    # Health and Status Methods
    def get_health(self) -> HealthStatus:
        """Get the health status of the bridge."""
        response = self.client.get("/health")
        data = self._handle_response(response)
        return HealthStatus(**data)
    
    async def aget_health(self) -> HealthStatus:
        """Async version of get_health."""
        response = await self.async_client.get("/health")
        data = self._handle_response(response)
        return HealthStatus(**data)
    
    def list_schemas(self) -> SchemaListResponse:
        """List available Protocol Buffer schemas."""
        response = self.client.get("/schema/list")
        data = self._handle_response(response)
        return SchemaListResponse(**data)
    
    async def alist_schemas(self) -> SchemaListResponse:
        """Async version of list_schemas."""
        response = await self.async_client.get("/schema/list")
        data = self._handle_response(response)
        return SchemaListResponse(**data)
    
    # Agent Methods
    def send_message(
        self,
        agent_id: str,
        content: str,
        message_type: str = "TEXT",
        options: Optional[MessageOptions] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> SendMessageResponse:
        """Send a message to an agent.
        
        Args:
            agent_id: ID of the target agent
            content: Message content
            message_type: Type of message (TEXT, COMMAND, etc.)
            options: Message options (timeout, streaming, etc.)
            metadata: Additional metadata
        
        Returns:
            SendMessageResponse with the agent's response
        """
        message = Message(content=content, type=message_type)
        request_data = SendMessageRequest(
            agent_id=agent_id,
            message=message,
            options=options or MessageOptions(),
            metadata=metadata or {}
        )
        
        response = self.client.post(
            "/agents/message",
            json=request_data.dict(exclude_none=True)
        )
        data = self._handle_response(response)
        return SendMessageResponse(**data)
    
    async def asend_message(
        self,
        agent_id: str,
        content: str,
        message_type: str = "TEXT",
        options: Optional[MessageOptions] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> SendMessageResponse:
        """Async version of send_message."""
        message = Message(content=content, type=message_type)
        request_data = SendMessageRequest(
            agent_id=agent_id,
            message=message,
            options=options or MessageOptions(),
            metadata=metadata or {}
        )
        
        response = await self.async_client.post(
            "/agents/message",
            json=request_data.dict(exclude_none=True)
        )
        data = self._handle_response(response)
        return SendMessageResponse(**data)
    
    def stream_message(
        self,
        agent_id: str,
        content: str,
        message_type: str = "TEXT",
        options: Optional[MessageOptions] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Stream a message to an agent and receive chunked responses.
        
        Args:
            agent_id: ID of the target agent
            content: Message content
            message_type: Type of message
            options: Message options
            metadata: Additional metadata
        
        Yields:
            Message chunks as they arrive
        """
        message = Message(content=content, type=message_type)
        options = options or MessageOptions()
        options.stream_response = True
        
        request_data = SendMessageRequest(
            agent_id=agent_id,
            message=message,
            options=options,
            metadata=metadata or {}
        )
        
        with self.client.stream(
            "POST",
            "/agents/message/stream",
            json=request_data.dict(exclude_none=True)
        ) as response:
            self._handle_response(response)
            
            for line in response.iter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON chunk: {line}")
    
    async def astream_message(
        self,
        agent_id: str,
        content: str,
        message_type: str = "TEXT",
        options: Optional[MessageOptions] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async version of stream_message."""
        message = Message(content=content, type=message_type)
        options = options or MessageOptions()
        options.stream_response = True
        
        request_data = SendMessageRequest(
            agent_id=agent_id,
            message=message,
            options=options,
            metadata=metadata or {}
        )
        
        async with self.async_client.stream(
            "POST",
            "/agents/message/stream",
            json=request_data.dict(exclude_none=True)
        ) as response:
            self._handle_response(response)
            
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON chunk: {line}")
    
    def list_agents(
        self,
        filter: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> ListAgentsResponse:
        """List available agents.
        
        Args:
            filter: Optional filter string
            page_size: Number of agents per page
            page_token: Pagination token
            type_filter: Filter by agent type
            status_filter: Filter by agent status
        
        Returns:
            ListAgentsResponse with agent list
        """
        params = {"page_size": page_size}
        if filter:
            params["filter"] = filter
        if page_token:
            params["page_token"] = page_token
        if type_filter:
            params["type_filter"] = type_filter
        if status_filter:
            params["status_filter"] = status_filter
        
        response = self.client.get("/agents", params=params)
        data = self._handle_response(response)
        return ListAgentsResponse(**data)
    
    async def alist_agents(
        self,
        filter: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> ListAgentsResponse:
        """Async version of list_agents."""
        params = {"page_size": page_size}
        if filter:
            params["filter"] = filter
        if page_token:
            params["page_token"] = page_token
        if type_filter:
            params["type_filter"] = type_filter
        if status_filter:
            params["status_filter"] = status_filter
        
        response = await self.async_client.get("/agents", params=params)
        data = self._handle_response(response)
        return ListAgentsResponse(**data)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a specific agent."""
        response = self.client.get(f"/agents/{agent_id}/status")
        return self._handle_response(response)
    
    async def aget_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Async version of get_agent_status."""
        response = await self.async_client.get(f"/agents/{agent_id}/status")
        return self._handle_response(response)
    
    def create_agent(self, agent: Agent) -> Dict[str, Any]:
        """Create a new agent."""
        request_data = CreateAgentRequest(agent=agent)
        response = self.client.post(
            "/agents",
            json=request_data.dict(exclude_none=True)
        )
        return self._handle_response(response)
    
    async def acreate_agent(self, agent: Agent) -> Dict[str, Any]:
        """Async version of create_agent."""
        request_data = CreateAgentRequest(agent=agent)
        response = await self.async_client.post(
            "/agents",
            json=request_data.dict(exclude_none=True)
        )
        return self._handle_response(response)
    
    # Task Methods
    def execute_task(self, task: Task, stream_updates: bool = False) -> Dict[str, Any]:
        """Execute a task across multiple agents."""
        request_data = ExecuteTaskRequest(task=task, stream_updates=stream_updates)
        response = self.client.post(
            "/tasks/execute",
            json=request_data.dict(exclude_none=True)
        )
        return self._handle_response(response)
    
    async def aexecute_task(self, task: Task, stream_updates: bool = False) -> Dict[str, Any]:
        """Async version of execute_task."""
        request_data = ExecuteTaskRequest(task=task, stream_updates=stream_updates)
        response = await self.async_client.post(
            "/tasks/execute",
            json=request_data.dict(exclude_none=True)
        )
        return self._handle_response(response)
    
    def stream_task_updates(self, task: Task) -> Iterator[TaskUpdate]:
        """Stream task execution updates."""
        request_data = ExecuteTaskRequest(task=task, stream_updates=True)
        
        with self.client.stream(
            "POST",
            "/tasks/execute/stream",
            json=request_data.dict(exclude_none=True)
        ) as response:
            self._handle_response(response)
            
            for line in response.iter_lines():
                if line.strip():
                    try:
                        update_data = json.loads(line)
                        yield TaskUpdate(**update_data)
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Invalid task update: {line}, error: {e}")
    
    async def astream_task_updates(self, task: Task) -> AsyncIterator[TaskUpdate]:
        """Async version of stream_task_updates."""
        request_data = ExecuteTaskRequest(task=task, stream_updates=True)
        
        async with self.async_client.stream(
            "POST",
            "/tasks/execute/stream",
            json=request_data.dict(exclude_none=True)
        ) as response:
            self._handle_response(response)
            
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        update_data = json.loads(line)
                        yield TaskUpdate(**update_data)
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Invalid task update: {line}, error: {e}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task."""
        response = self.client.get(f"/tasks/{task_id}/status")
        return self._handle_response(response)
    
    async def aget_task_status(self, task_id: str) -> Dict[str, Any]:
        """Async version of get_task_status."""
        response = await self.async_client.get(f"/tasks/{task_id}/status")
        return self._handle_response(response)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running task."""
        response = self.client.post(f"/tasks/{task_id}/cancel")
        return self._handle_response(response)
    
    async def acancel_task(self, task_id: str) -> Dict[str, Any]:
        """Async version of cancel_task."""
        response = await self.async_client.post(f"/tasks/{task_id}/cancel")
        return self._handle_response(response)


# Convenience functions
def create_sdk(base_url: str = "http://localhost:8000", **kwargs) -> AgentSDK:
    """Create an AgentSDK instance.
    
    Args:
        base_url: Base URL of the Agent Bridge API
        **kwargs: Additional arguments for AgentSDK
    
    Returns:
        Configured AgentSDK instance
    """
    return AgentSDK(base_url=base_url, **kwargs)


@asynccontextmanager
async def async_sdk(base_url: str = "http://localhost:8000", **kwargs):
    """Async context manager for AgentSDK.
    
    Args:
        base_url: Base URL of the Agent Bridge API
        **kwargs: Additional arguments for AgentSDK
    
    Yields:
        Configured AgentSDK instance
    """
    sdk = AgentSDK(base_url=base_url, **kwargs)
    try:
        yield sdk
    finally:
        await sdk.aclose() 