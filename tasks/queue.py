"""파일 기반 태스크 큐 - 에이전트 간 통신 레이어"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .models import AgentType, Task, TaskStatus


class TaskQueue:
    """
    파일 시스템 기반 태스크 큐.

    구조:
      .tasks/
        pending/    <- 대기 중인 태스크
        active/     <- 처리 중인 태스크
        done/       <- 완료된 태스크
        failed/     <- 실패한 태스크
    """

    def __init__(self, base_dir: str = ".tasks") -> None:
        self.base = Path(base_dir)
        for sub in ("pending", "active", "done", "failed"):
            (self.base / sub).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 쓰기
    # ------------------------------------------------------------------

    def enqueue(self, task: Task) -> None:
        """태스크를 대기 큐에 추가"""
        path = self.base / "pending" / f"{task.id}.json"
        path.write_text(task.model_dump_json(indent=2), encoding="utf-8")

    def claim(self, task_id: str) -> Optional[Task]:
        """워커가 태스크를 가져가 active 상태로 전환"""
        src = self.base / "pending" / f"{task_id}.json"
        dst = self.base / "active" / f"{task_id}.json"
        if not src.exists():
            return None
        task = Task.model_validate_json(src.read_text())
        task.mark_in_progress()
        dst.write_text(task.model_dump_json(indent=2), encoding="utf-8")
        src.unlink()
        return task

    def complete(self, task: Task, result: str) -> None:
        """태스크 완료 처리"""
        task.mark_completed(result)
        self._move(task, "done")

    def fail(self, task: Task, error: str) -> None:
        """태스크 실패 처리"""
        task.mark_failed(error)
        self._move(task, "failed")

    # ------------------------------------------------------------------
    # 읽기
    # ------------------------------------------------------------------

    def list_pending(self, agent: Optional[AgentType] = None) -> list[Task]:
        """대기 중인 태스크 조회 (에이전트 타입으로 필터링 가능)"""
        return self._load_dir("pending", agent)

    def list_active(self, agent: Optional[AgentType] = None) -> list[Task]:
        return self._load_dir("active", agent)

    def list_done(self) -> list[Task]:
        return self._load_dir("done")

    def get(self, task_id: str) -> Optional[Task]:
        """ID로 태스크 조회 (모든 상태 검색)"""
        for sub in ("pending", "active", "done", "failed"):
            path = self.base / sub / f"{task_id}.json"
            if path.exists():
                return Task.model_validate_json(path.read_text())
        return None

    def are_dependencies_met(self, task: Task) -> bool:
        """태스크의 선행 의존성이 모두 완료되었는지 확인"""
        for dep_id in task.dependencies:
            dep = self.get(dep_id)
            if dep is None or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    def get_dependency_results(self, task: Task) -> dict[str, str]:
        """의존 태스크들의 결과를 수집하여 반환"""
        results: dict[str, str] = {}
        for dep_id in task.dependencies:
            dep = self.get(dep_id)
            if dep and dep.result:
                results[dep_id] = dep.result
        return results

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _move(self, task: Task, target_dir: str) -> None:
        for sub in ("pending", "active"):
            src = self.base / sub / f"{task.id}.json"
            if src.exists():
                src.unlink()
        dst = self.base / target_dir / f"{task.id}.json"
        dst.write_text(task.model_dump_json(indent=2), encoding="utf-8")

    def _load_dir(self, subdir: str, agent: Optional[AgentType] = None) -> list[Task]:
        tasks = []
        for path in (self.base / subdir).glob("*.json"):
            task = Task.model_validate_json(path.read_text())
            if agent is None or task.assigned_to == agent:
                tasks.append(task)
        return sorted(tasks, key=lambda t: t.created_at)
