"""
Codex Worker - OpenAI 기반 코딩 실행 에이전트

역할:
  - Claude 오케스트레이터로부터 태스크를 받아 실제 코드 구현
  - 병렬 처리 지원 (asyncio)
  - 코드, 테스트, 리팩토링 태스크 처리
"""

from __future__ import annotations

import asyncio
import textwrap
from typing import Optional

from openai import AsyncOpenAI

from tasks import AgentType, Task, TaskQueue, TaskType


SYSTEM_PROMPT = """당신은 숙련된 소프트웨어 엔지니어입니다.

당신의 역할:
- 주어진 스펙에 따라 정확하고 깔끔한 코드를 작성
- 코드는 바로 실행 가능한 완성된 형태로 제공
- 파일 경로와 코드를 명확히 구분하여 출력

출력 형식:
```python
# 파일: src/example.py
<코드 내용>
```

항상 실제 동작하는 코드를 작성하고, 불필요한 설명은 최소화하세요."""


class CodexWorker:
    def __init__(
        self,
        queue: TaskQueue,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        parallel_limit: int = 3,
    ) -> None:
        self.queue = queue
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        self.semaphore = asyncio.Semaphore(parallel_limit)

    # ------------------------------------------------------------------
    # 단일 태스크 처리
    # ------------------------------------------------------------------

    async def process_task(self, task: Task) -> str:
        """태스크 하나를 처리하고 결과 반환"""
        async with self.semaphore:
            claimed = self.queue.claim(task.id)
            if claimed is None:
                raise RuntimeError(f"태스크 {task.id}를 가져올 수 없습니다")

            # 의존 태스크 결과 수집
            dep_results = self.queue.get_dependency_results(claimed)
            prompt = self._build_prompt(claimed, dep_results)

            try:
                result = await self._call_openai(prompt, claimed.type)
                self.queue.complete(claimed, result)
                return result
            except Exception as exc:
                self.queue.fail(claimed, str(exc))
                raise

    # ------------------------------------------------------------------
    # 병렬 처리
    # ------------------------------------------------------------------

    async def process_ready_tasks(self) -> list[tuple[Task, str]]:
        """
        의존성이 충족된 대기 태스크를 모두 병렬로 처리.
        (Claude → 에게 할당된 태스크는 스킵)
        """
        pending = self.queue.list_pending(agent=AgentType.CODEX)
        ready = [t for t in pending if self.queue.are_dependencies_met(t)]

        if not ready:
            return []

        tasks_coroutines = [self.process_task(t) for t in ready]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)

        outcomes = []
        for task, result in zip(ready, results):
            if isinstance(result, Exception):
                print(f"[Codex] 태스크 실패: {task.title} - {result}")
            else:
                outcomes.append((task, result))
                print(f"[Codex] 완료: {task.title}")
        return outcomes

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    async def _call_openai(self, prompt: str, task_type: TaskType) -> str:
        # 태스크 타입별 시스템 프롬프트 조정
        system = SYSTEM_PROMPT
        if task_type == TaskType.TEST:
            system += "\n\n특히 pytest를 사용한 단위 테스트와 엣지 케이스 테스트에 집중하세요."
        elif task_type == TaskType.REFACTOR:
            system += "\n\n기존 코드의 기능은 유지하면서 가독성과 성능을 개선하세요."

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _build_prompt(task: Task, dep_results: dict[str, str]) -> str:
        parts = [
            f"## 태스크: {task.title}",
            f"\n{task.description}",
        ]

        if dep_results:
            parts.append("\n## 선행 태스크 결과 (참고)")
            for dep_id, result in dep_results.items():
                parts.append(f"\n### {dep_id}\n{result[:1000]}")

        if task.context:
            parts.append(f"\n## 추가 컨텍스트\n{task.context}")

        return "\n".join(parts)
