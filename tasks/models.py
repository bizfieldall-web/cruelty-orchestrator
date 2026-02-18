"""태스크 데이터 모델 정의"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW = "review"          # 오케스트레이터 검토 대기


class TaskType(str, Enum):
    PLAN = "plan"              # 아키텍처/계획 수립 (Claude)
    CODE = "code"              # 코드 구현 (Codex)
    TEST = "test"              # 테스트 작성 (Codex)
    REFACTOR = "refactor"      # 리팩토링 (Codex)
    REVIEW = "review"          # 코드 리뷰 (Claude)
    INTEGRATE = "integrate"    # 결과 통합 (Claude)


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"   # Claude
    CODEX = "codex"                 # OpenAI Codex


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: TaskType
    assigned_to: AgentType
    title: str
    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)   # task id 목록
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def mark_in_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self, result: str) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = datetime.utcnow()


class TaskPlan(BaseModel):
    """오케스트레이터가 생성하는 전체 태스크 계획"""
    goal: str
    tasks: list[Task]
    created_at: datetime = Field(default_factory=datetime.utcnow)
