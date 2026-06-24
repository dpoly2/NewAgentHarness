from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class RunRequest(BaseModel):
    agent_id: str
    project: str
    graph: str = "reflexion"
    task: str
    max_revisions: int = 2
    priority: str = "normal"


class TodoCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    project: str = ""
    due_date: str = ""
    tags: List[Any] = Field(default_factory=list)
    source: str = "user"


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    project: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[Any]] = None


class TripCreate(BaseModel):
    name: str
    destination: str
    depart_date: str = ""
    return_date: str = ""
    status: str = "planning"
    budget: float = 0.0
    notes: str = ""


class TripUpdate(BaseModel):
    name: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    notes: Optional[str] = None


class ConnectorCreate(BaseModel):
    label: str
    email_address: str
    provider: str = "imap"
    auth_type: str = "password"
    imap_host: str = ""
    imap_port: int = 993
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    credentials: dict = Field(default_factory=dict)
    oauth_client_id: str = ""
    oauth_client_secret: str = ""


class ConnectorUpdate(BaseModel):
    label: Optional[str] = None
    email_address: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    credentials: Optional[dict] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    status: Optional[str] = None


class ProjectCreate(BaseModel):
    slug: str
    name: str
    description: str = ""
    status: str = "active"
    lead_agent: str = ""
    tags: List[Any] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    lead_agent: Optional[str] = None
    tags: Optional[List[Any]] = None


class ClientCreate(BaseModel):
    slug: str
    name: str
    business_type: str = ""
    service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    engagement: str = "retainer"
    status: str = "active"
    project_slug: str = ""
    notes: str = ""


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    service: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    engagement: Optional[str] = None
    status: Optional[str] = None
    project_slug: Optional[str] = None
    notes: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str
    agent_id: str = ""


class ConversationCreate(BaseModel):
    title: str
    slug: str = "global"


class SchedulerJobCreate(BaseModel):
    agent_id: str
    project: str
    graph: str = "reflexion"
    task: str
    run_type: str = "cron"
    cron_expr: str = ""
    interval_sec: int = 0


class ConfigUpdate(BaseModel):
    data: dict


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class MemoryUpdate(BaseModel):
    data: dict


class AgentUpsert(BaseModel):
    agent_id: str
    name: str
    type: str = "specialist"
    role: str = ""
    description: str = ""
    project_slug: str = ""
    capabilities: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    status: str = "active"
    system_prompt: str = ""
    config: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    project_slug: Optional[str] = None
    capabilities: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    status: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[dict] = None
    metadata: Optional[dict] = None


class AutomationCreate(BaseModel):
    slug: str
    name: str
    description: str = ""
    project_slug: str = ""
    agent_id: str = ""
    trigger_type: str = "manual"
    trigger_config: dict = Field(default_factory=dict)
    steps: List[Any] = Field(default_factory=list)
    status: str = "active"


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_slug: Optional[str] = None
    agent_id: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None
    steps: Optional[List[Any]] = None
    status: Optional[str] = None


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    source: str = ""
    source_type: str = "manual"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    project_slug: str = ""
    agent_id: str = ""


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    project_slug: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentCreate(BaseModel):
    title: str
    doc_type: str = "general"
    content: str = ""
    format: str = "markdown"
    project_slug: str = ""
    client_id: str = ""
    tags: List[str] = Field(default_factory=list)
    created_by: str = ""


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class IntegrationUpsert(BaseModel):
    name: str
    provider: str
    entity_type: str = "global"
    entity_id: str = ""
    auth_type: str = "oauth2"
    credentials: dict = Field(default_factory=dict)
    scope: str = ""
    status: str = "pending"
    metadata: dict = Field(default_factory=dict)


class AutomationDocCreate(BaseModel):
    automation_id: str = ""
    run_id: str = ""
    title: str = ""
    doc_type: str = "report"
    content: str = ""
    status: str = "draft"
    reviewed_by: str = ""
    review_notes: str = ""


class InezChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ModelToggle(BaseModel):
    provider: str
    model_id: str
    enabled: bool


class ModelRouteRequest(BaseModel):
    task_type: str
    agent_id: str = ""


class ReportRunRequest(BaseModel):
    job_id: str
    extra_context: str = ""


class MemoryFactBody(BaseModel):
    category: str
    key: str
    value: str
    importance: int = 5
    source: str = "user"
    confidence: float = 1.0


class SandboxExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    data_files: Optional[list[Any]] = None
