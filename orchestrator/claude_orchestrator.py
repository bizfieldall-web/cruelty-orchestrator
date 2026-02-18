"""
Claude Orchestrator - 전체 앱 개발 지휘관

역할:
  1. 사용자 목표를 분석하여 태스크 계획 수립
  2. 태스크를 Codex 워커에게 분배
  3. 완료된 결과를 검토하고 통합
  4. 다음 단계를 동적으로 결정
"""

from __future__ import annotations

import json
import textwrap
from typing import Any, Optional

import anthropic

from tasks import AgentType, Task, TaskPlan, TaskStatus, TaskType, TaskQueue


SYSTEM_PROMPT = """당신은 소프트웨어 개발 팀의 수석 아키텍트이자 오케스트레이터입니다.

당신의 역할:
- 사용자의 앱 개발 목표를 분석하고 세부 태스크로 분해
- 각 태스크를 Codex 워커에게 명확한 스펙으로 위임
- 워커의 결과물을 검토하고 피드백 제공
- 전체 프로젝트 진행 상황을 추적하고 조율

태스크 계획 시 JSON 형식을 사용합니다:
{
  "tasks": [
    {
      "type": "code|test|refactor|review",
      "assigned_to": "codex",
      "title": "태스크 제목",
      "description": "상세 구현 스펙 (Codex가 이해할 수 있도록 명확하게)",
      "dependencies": []  // 선행 태스크 ID 목록
    }
  ]
}"""


class ClaudeOrchestrator:
    def __init__(
        self,
        queue: TaskQueue,
        model: str = "claude-opus-4-6",
        api_key: Optional[str] = None,
    ) -> None:
        self.queue = queue
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self._conversation: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 1단계: 목표 → 태스크 계획
    # ------------------------------------------------------------------

    def plan(self, goal: str) -> TaskPlan:
        """사용자 목표를 분석하여 태스크 계획 수립"""
        prompt = textwrap.dedent(f"""
            다음 앱 개발 목표를 분석하고 구체적인 태스크 계획을 수립해주세요.

            목표: {goal}

            요구사항:
            - 태스크를 논리적 순서로 나눠주세요 (기초 → 핵심 → 부가기능)
            - 각 태스크는 Codex 워커 하나가 독립적으로 처리할 수 있는 단위로 분리
            - 의존 관계가 있는 태스크는 dependencies 필드에 선행 태스크 인덱스를 명시
            - description은 Codex가 바로 구현할 수 있을 정도로 상세하게 작성

            반드시 JSON만 출력하세요 (설명 텍스트 없이).
        """).strip()

        response = self._call_claude(prompt)

        # JSON 파싱
        raw_plan = self._parse_json(response)
        tasks = []
        id_map: dict[int, str] = {}

        for idx, raw_task in enumerate(raw_plan.get("tasks", [])):
            task = Task(
                type=TaskType(raw_task.get("type", "code")),
                assigned_to=AgentType(raw_task.get("assigned_to", "codex")),
                title=raw_task["title"],
                description=raw_task["description"],
                context=raw_task.get("context", {}),
                dependencies=[
                    id_map[dep_idx]
                    for dep_idx in raw_task.get("dependencies", [])
                    if dep_idx in id_map
                ],
            )
            id_map[idx] = task.id
            tasks.append(task)

        plan = TaskPlan(goal=goal, tasks=tasks)

        # 큐에 등록
        for task in plan.tasks:
            self.queue.enqueue(task)

        return plan

    # ------------------------------------------------------------------
    # 2단계: 완료된 태스크 검토
    # ------------------------------------------------------------------

    def review_result(self, task: Task) -> str:
        """Codex 워커가 완료한 결과를 검토하고 피드백 반환"""
        prompt = textwrap.dedent(f"""
            Codex 워커가 다음 태스크를 완료했습니다. 결과를 검토해주세요.

            ## 태스크
            제목: {task.title}
            설명: {task.description}

            ## Codex 결과물
            {task.result}

            검토 기준:
            - 요구사항을 모두 충족했는가?
            - 코드 품질 (가독성, 구조, 명명 규칙)
            - 엣지 케이스 처리
            - 보안 취약점 여부

            간결하게 피드백을 작성하고, 통과/재작업 여부를 명시하세요.
            형식: PASS 또는 REWORK: <이유>
        """).strip()

        return self._call_claude(prompt)

    # ------------------------------------------------------------------
    # 3단계: 전체 통합 요약
    # ------------------------------------------------------------------

    def integrate(self, plan: TaskPlan) -> str:
        """모든 태스크 완료 후 최종 통합 요약 생성"""
        completed = [t for t in plan.tasks if t.status == TaskStatus.COMPLETED]
        results_summary = "\n\n".join(
            f"### {t.title}\n{(t.result or '')[:500]}"
            for t in completed
        )

        prompt = textwrap.dedent(f"""
            모든 개발 태스크가 완료되었습니다. 최종 통합 요약을 작성해주세요.

            ## 목표
            {plan.goal}

            ## 완료된 태스크 결과
            {results_summary}

            다음을 포함한 최종 보고서를 작성하세요:
            1. 구현된 기능 요약
            2. 프로젝트 구조 설명
            3. 실행 방법
            4. 추가 개선 가능 사항
        """).strip()

        return self._call_claude(prompt)

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _call_claude(self, user_message: str) -> str:
        self._conversation.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=self._conversation,
        )
        assistant_message = response.content[0].text
        self._conversation.append({"role": "assistant", "content": assistant_message})
        return assistant_message

    @staticmethod
    def _parse_json(text: str) -> dict:
        # 코드 블록 제거
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return json.loads(text)
