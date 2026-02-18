"""
사용 예시 - 프로그래밍 방식으로 에이전트 팀 직접 사용

이 파일은 CLI 없이 Python 코드에서 직접 에이전트를 제어하는 방법을 보여줍니다.
"""

import asyncio
import os

from dotenv import load_dotenv

from orchestrator import ClaudeOrchestrator
from tasks import TaskQueue
from workers import CodexWorker

load_dotenv()


async def build_todo_app() -> None:
    """
    예시: Claude가 지휘하고 Codex 팀이 Todo 앱을 개발하는 과정
    """

    queue = TaskQueue(base_dir=".tasks-demo")
    orchestrator = ClaudeOrchestrator(
        queue=queue,
        model="claude-opus-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    worker = CodexWorker(
        queue=queue,
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        parallel_limit=3,
    )

    goal = "FastAPI + SQLite를 사용한 RESTful Todo API 앱. CRUD 기능과 pytest 테스트 포함."

    print("=" * 60)
    print("Claude가 태스크를 계획합니다...")
    print("=" * 60)

    # 1단계: Claude가 계획 수립
    plan = orchestrator.plan(goal)

    print(f"\n총 {len(plan.tasks)}개 태스크 생성:")
    for i, task in enumerate(plan.tasks, 1):
        deps = f" (의존: {task.dependencies})" if task.dependencies else ""
        print(f"  {i}. [{task.assigned_to.value}] {task.title}{deps}")

    print("\n" + "=" * 60)
    print("Codex 워커 팀이 병렬로 구현을 시작합니다...")
    print("=" * 60)

    # 2단계: Codex 워커들이 의존성 순서에 따라 처리
    round_num = 0
    while True:
        round_num += 1
        print(f"\n[Round {round_num}]")

        outcomes = await worker.process_ready_tasks()
        if not outcomes:
            print("처리할 준비된 태스크가 없습니다. 완료!")
            break

        for task, result in outcomes:
            print(f"\n  완료: {task.title}")
            print(f"  결과 미리보기:\n{result[:200]}...")

            # Claude가 검토
            review = orchestrator.review_result(task)
            print(f"  Claude 검토: {review[:100]}")

    # 3단계: 최종 통합 보고서
    print("\n" + "=" * 60)
    print("Claude가 최종 통합 보고서를 작성합니다...")
    print("=" * 60)
    summary = orchestrator.integrate(plan)
    print(f"\n{summary}")


if __name__ == "__main__":
    asyncio.run(build_todo_app())
