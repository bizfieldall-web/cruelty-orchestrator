"""
크루엘티 오케스트레이터 - CLI 진입점

사용법:
  python main.py run "Todo 앱을 FastAPI + SQLite로 만들어줘"
  python main.py status
  python main.py plan "목표"
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

from orchestrator import ClaudeOrchestrator
from tasks import TaskQueue, TaskStatus
from workers import CodexWorker

load_dotenv()

app = typer.Typer(
    name="cruelty",
    help="Claude + Codex 멀티 에이전트 앱 개발 오케스트레이터",
)
console = Console()


def _get_queue() -> TaskQueue:
    return TaskQueue(base_dir=".tasks")


def _get_orchestrator(queue: TaskQueue) -> ClaudeOrchestrator:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]오류: ANTHROPIC_API_KEY 환경변수를 설정하세요[/red]")
        raise typer.Exit(1)
    return ClaudeOrchestrator(queue=queue, api_key=api_key)


def _get_worker(queue: TaskQueue) -> CodexWorker:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]오류: OPENAI_API_KEY 환경변수를 설정하세요[/red]")
        raise typer.Exit(1)
    return CodexWorker(queue=queue, api_key=api_key)


# ------------------------------------------------------------------
# 명령어: run (계획 → 실행 → 통합 전체 파이프라인)
# ------------------------------------------------------------------

@app.command()
def run(
    goal: str = typer.Argument(..., help="개발할 앱의 목표를 자유롭게 설명하세요"),
    dry_run: bool = typer.Option(False, "--dry-run", help="계획만 출력하고 실행하지 않음"),
) -> None:
    """Claude가 계획을 세우고 Codex 팀이 구현하는 전체 파이프라인을 실행합니다."""

    queue = _get_queue()
    orchestrator = _get_orchestrator(queue)
    worker = _get_worker(queue)

    # 1단계: Claude가 태스크 계획 수립
    console.print(Panel(f"[bold cyan]목표[/bold cyan]: {goal}", title="크루엘티 오케스트레이터"))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        plan_task = progress.add_task("Claude가 태스크 계획을 수립하는 중...", total=None)
        plan = orchestrator.plan(goal)
        progress.update(plan_task, completed=True)

    # 계획 출력
    table = Table(title=f"태스크 계획 ({len(plan.tasks)}개)", show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("타입", style="cyan")
    table.add_column("제목")
    table.add_column("담당", style="yellow")
    table.add_column("의존성", style="dim")

    for task in plan.tasks:
        table.add_row(
            task.id,
            task.type.value,
            task.title,
            task.assigned_to.value,
            ", ".join(task.dependencies) if task.dependencies else "-",
        )
    console.print(table)

    if dry_run:
        console.print("[yellow]--dry-run 모드: 계획만 출력하고 종료합니다[/yellow]")
        return

    # 2단계: Codex 워커들이 병렬 실행
    console.print("\n[bold green]Codex 워커 팀 실행 시작...[/bold green]")

    async def _run_workers() -> None:
        max_rounds = 10
        for round_num in range(max_rounds):
            outcomes = await worker.process_ready_tasks()
            if not outcomes:
                # 더 이상 처리할 준비된 태스크 없음
                break
            console.print(f"  [round {round_num + 1}] {len(outcomes)}개 태스크 완료")

            # Claude가 각 결과 검토
            for task, _ in outcomes:
                review = orchestrator.review_result(task)
                prefix = "[green]PASS[/green]" if review.startswith("PASS") else "[yellow]REWORK[/yellow]"
                console.print(f"  {prefix} {task.title}: {review[:80]}")

    asyncio.run(_run_workers())

    # 3단계: Claude가 결과 통합
    console.print("\n[bold cyan]Claude가 최종 결과를 통합하는 중...[/bold cyan]")
    summary = orchestrator.integrate(plan)
    console.print(Panel(summary, title="최종 통합 보고서", border_style="green"))


# ------------------------------------------------------------------
# 명령어: plan (계획만 확인)
# ------------------------------------------------------------------

@app.command()
def plan(
    goal: str = typer.Argument(..., help="개발 목표"),
) -> None:
    """Claude에게 태스크 계획만 세우게 합니다 (실행 없이)."""
    run(goal=goal, dry_run=True)


# ------------------------------------------------------------------
# 명령어: status (현재 큐 상태 확인)
# ------------------------------------------------------------------

@app.command()
def status() -> None:
    """현재 태스크 큐 상태를 확인합니다."""
    queue = _get_queue()

    for label, loader, color in [
        ("대기 중 (PENDING)", lambda: queue.list_pending(), "yellow"),
        ("진행 중 (IN_PROGRESS)", lambda: queue.list_active(), "blue"),
        ("완료 (DONE)", lambda: queue.list_done(), "green"),
    ]:
        tasks = loader()
        if not tasks:
            continue
        table = Table(title=label, show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("제목")
        table.add_column("담당", style=color)
        table.add_column("타입")
        for t in tasks:
            table.add_row(t.id, t.title, t.assigned_to.value, t.type.value)
        console.print(table)


# ------------------------------------------------------------------
# 명령어: clear (태스크 큐 초기화)
# ------------------------------------------------------------------

@app.command()
def clear() -> None:
    """태스크 큐를 초기화합니다."""
    import shutil
    if os.path.exists(".tasks"):
        shutil.rmtree(".tasks")
        console.print("[green]태스크 큐가 초기화되었습니다[/green]")
    else:
        console.print("[dim]초기화할 태스크 큐가 없습니다[/dim]")


if __name__ == "__main__":
    app()
