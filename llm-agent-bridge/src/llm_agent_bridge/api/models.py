"""Pydantic models for REST API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


# Enums matching protobuf definitions
class MessageType(str, Enum):
    TEXT = "TEXT"
    COMMAND = "COMMAND"
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"
    SYSTEM = "SYSTEM"
    FUNCTION_CALL = "FUNCTION_CALL"
    FUNCTION_RESULT = "FUNCTION_RESULT"


class MessageStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentType(str, Enum):
    CHAT = "CHAT"
    FUNCTION = "FUNCTION"
    TOOL = "TOOL"
    ORCHESTRATOR = "ORCHESTRATOR"
    ANALYZER = "ANALYZER"
    GENERATOR = "GENERATOR"


class AgentStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    BUSY = "BUSY"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class TaskType(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"
    PIPELINE = "PIPELINE"


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class TaskStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# Base models
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = None
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Message models
class Attachment(BaseModel):
    """Message attachment model."""
    id: str
    name: str
    mime_type: str
    data: Optional[bytes] = None
    url: Optional[str] = None
    size: Optional[int] = None


class MessageOptions(BaseModel):
    """Message options model."""
    timeout_seconds: Optional[int] = Field(default=30, ge=1, le=300)
    stream_response: bool = False
    max_tokens: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    stop_sequences: List[str] = Field(default=[])
    include_metadata: bool = True


class Message(BaseModel):
    """Message model."""
    id: Optional[str] = None
    content: str = Field(..., min_length=1)
    type: MessageType = MessageType.TEXT
    format: str = Field(default="text", regex=r"^(text|json|markdown|html)$")
    attachments: List[Attachment] = Field(default=[])
    parameters: Dict[str, Any] = Field(default={})
    created_at: Optional[datetime] = None


class MessageChunk(BaseModel):
    """Streaming message chunk model."""
    message_id: str
    chunk_id: str
    content: str
    is_final: bool = False
    metadata: Dict[str, str] = Field(default={})


# Agent models
class AgentCapabilities(BaseModel):
    """Agent capabilities model."""
    supported_formats: List[str] = Field(default=["text", "json"])
    supported_languages: List[str] = Field(default=["en"])
    supports_streaming: bool = False
    supports_function_calling: bool = False
    max_concurrent_requests: int = Field(default=1, ge=1)
    tools: List[str] = Field(default=[])


class AgentConfig(BaseModel):
    """Agent configuration model."""
    model: str
    parameters: Dict[str, Any] = Field(default={})
    system_prompts: List[str] = Field(default=[])
    max_tokens: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=30, ge=1)


class AgentHealth(BaseModel):
    """Agent health model."""
    is_healthy: bool
    issues: List[str] = Field(default=[])
    last_check: Optional[datetime] = None
    uptime_seconds: Optional[int] = None


class AgentMetrics(BaseModel):
    """Agent metrics model."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    current_load: float = 0.0
    last_activity: Optional[datetime] = None


class Agent(BaseModel):
    """Agent model."""
    id: str = Field(..., regex=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    type: AgentType = AgentType.CHAT
    status: AgentStatus = AgentStatus.INITIALIZING
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    config: AgentConfig
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, str] = Field(default={})


# Task models
class TaskStep(BaseModel):
    """Task step model."""
    id: str
    agent_id: str
    action: str
    parameters: Dict[str, Any] = Field(default={})
    status: TaskStepStatus = TaskStepStatus.PENDING
    result: Optional[Any] = None
    dependencies: List[str] = Field(default=[])


class Task(BaseModel):
    """Task model."""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    type: TaskType = TaskType.SEQUENTIAL
    status: TaskStatus = TaskStatus.CREATED
    steps: List[TaskStep] = Field(..., min_items=1)
    parameters: Dict[str, Any] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Task update model for streaming."""
    task_id: str
    status: TaskStatus
    step_id: Optional[str] = None
    step_status: Optional[TaskStepStatus] = None
    step_result: Optional[Any] = None
    progress: float = Field(ge=0.0, le=1.0)
    message: Optional[str] = None


# Request/Response models
class SendMessageRequest(BaseModel):
    """Send message request model."""
    agent_id: str = Field(..., regex=r"^[a-zA-Z0-9_-]+$")
    message: Message
    options: MessageOptions = Field(default_factory=MessageOptions)
    metadata: Dict[str, str] = Field(default={})


class SendMessageResponse(BaseResponse):
    """Send message response model."""
    message_id: str
    response: Message
    status: MessageStatus
    metadata: Dict[str, str] = Field(default={})


class AgentStatusResponse(BaseResponse):
    """Agent status response model."""
    agent: Agent
    health: AgentHealth
    metrics: AgentMetrics


class ListAgentsRequest(BaseModel):
    """List agents request model."""
    filter: Optional[str] = None
    page_size: int = Field(default=20, ge=1, le=100)
    page_token: Optional[str] = None
    type_filter: Optional[AgentType] = None
    status_filter: Optional[AgentStatus] = None


class ListAgentsResponse(BaseResponse):
    """List agents response model."""
    agents: List[Agent]
    next_page_token: Optional[str] = None
    total_count: int


class CreateAgentRequest(BaseModel):
    """Create agent request model."""
    agent: Agent


class CreateAgentResponse(BaseResponse):
    """Create agent response model."""
    agent: Agent


class UpdateAgentRequest(BaseModel):
    """Update agent request model."""
    agent: Agent
    update_fields: List[str] = Field(default=[])


class UpdateAgentResponse(BaseResponse):
    """Update agent response model."""
    agent: Agent


class ExecuteTaskRequest(BaseModel):
    """Execute task request model."""
    task: Task
    stream_updates: bool = False


class ExecuteTaskResponse(BaseResponse):
    """Execute task response model."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None


class TaskStatusResponse(BaseResponse):
    """Task status response model."""
    task: Task
    progress: float = Field(ge=0.0, le=1.0)


# Health and monitoring models
class HealthStatus(BaseModel):
    """Health status model."""
    status: str = Field(regex=r"^(healthy|degraded|unhealthy)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime_seconds: int
    checks: Dict[str, Dict[str, Any]] = Field(default={})


class SchemaInfo(BaseModel):
    """Schema information model."""
    version: str
    services: List[str]
    file_hash: str
    is_current: bool = False


class SchemaListResponse(BaseResponse):
    """Schema list response model."""
    schemas: List[SchemaInfo]
    current_version: Optional[str] = None


# WebSocket models
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(regex=r"^(message|event|status|error)$")
    agent_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketSubscription(BaseModel):
    """WebSocket subscription model."""
    agent_ids: List[str] = Field(default=[])
    event_types: List[str] = Field(default=[])
    filter: Optional[str] = None 