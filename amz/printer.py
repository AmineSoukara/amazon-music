"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

console = Console()
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=40),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    console=console,
)


def info(msg: str):
    console.print(f"[bold cyan][INFO][/bold cyan] {msg}")


def success(msg: str):
    console.print(f"[bold green][✔] {msg}[/bold green]")


def warning(msg: str):
    console.print(f"[bold yellow][!] {msg}[/bold yellow]")


def error(msg: str):
    console.print(f"[bold red][✘] {msg}[/bold red]")


def section(title: str):
    console.print(Panel(Text(title, justify="center", style="bold magenta")))


def print_trace(e: Exception):
    console.print_exception(show_locals=True)


def new_task(description: str, total: int):
    return progress.add_task(description=description, total=total)


def update_task(task_id: int, advance: int = 1):
    progress.update(task_id, advance=advance)


def start_progress():
    if not progress.live.is_started:
        progress.start()


def stop_progress():
    if progress.live.is_started:
        progress.stop()
