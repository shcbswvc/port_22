from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime
    preferences: Dict

@dataclass
class Task:
    id: Optional[int]
    user_id: int
    title: str
    category: str  # learning, health, personal, work
    importance: int  # 1-10
    notes: str
    task_type: str  # simple, complex
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
@dataclass
class GeneratedNotification:
    id: Optional[int]
    notification_id: str
    task_id: int
    hook_message: str
    expanded_content: Optional[str]
    next_step: str
    confidence_score: float
    generation_strategy: str
    timestamp: datetime
    llm_prompt_used: Optional[str] = None
    llm_response_raw: Optional[str] = None

@dataclass
class NotificationResponse:
    id: Optional[int]
    notification_id: str
    task_id: int
    user_action: str  # dismissed, clicked, expanded, acted
    response_time: float
    was_expanded: bool
    timestamp: datetime
    context: Dict
