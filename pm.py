#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.0",
#   "rich>=13.7.0",
# ]
# ///
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from database import Database
from datetime import datetime

console = Console()
db = Database()

VALID_STATUSES = ['todo', 'in-progress', 'done']
STATUS_SHORTCUTS = {
    't': 'todo',
    'i': 'in-progress',
    'd': 'done',
    'todo': 'todo',
    'in-progress': 'in-progress',
    'done': 'done'
}

def normalize_status(status: str) -> str:
    """Convert status shortcut to full status name."""
    if status is None:
        return None
    return STATUS_SHORTCUTS.get(status.lower(), status)

def format_status(status: str) -> Text:
    """Format status with colors."""
    colors = {
        'todo': 'yellow',
        'in-progress': 'blue',
        'done': 'green'
    }
    return Text(status, style=colors.get(status, 'white'))

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_str

@click.group()
def cli():
    """Simple project management tool for tracking tasks."""
    pass

# Project commands
@cli.group()
def project():
    """Manage projects."""
    pass

@project.command('create')
@click.argument('name')
def project_create(name):
    """Create a new project."""
    try:
        project_id = db.create_project(name)
        console.print(f"[green]✓[/green] Created project '{name}' (ID: {project_id})")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")

@project.command('list')
def project_list():
    """List all projects."""
    projects = db.list_projects()

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        return

    table = Table(title="Projects", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Name", style="green")
    table.add_column("Created", style="dim")

    for proj in projects:
        table.add_row(
            str(proj['id']),
            proj['name'],
            format_datetime(proj['created_at'])
        )

    console.print(table)

# Task commands
@cli.group()
def task():
    """Manage tasks."""
    pass

@task.command('create')
@click.argument('title')
@click.option('--project', '-p', help='Project name')
@click.option('--description', '-d', help='Task description')
def task_create(title, project, description):
    """Create a new task."""
    project_id = None

    if project:
        proj = db.get_project(project)
        if not proj:
            console.print(f"[red]✗[/red] Project '{project}' not found.")
            return
        project_id = proj['id']

    try:
        task_id = db.create_task(title, project_id, description)
        console.print(f"[green]✓[/green] Created task '{title}' (ID: {task_id})")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")

@task.command('list')
@click.option('--project', '-p', help='Filter by project name')
@click.option('--status', '-s', help='Filter by status (todo/t, in-progress/i, done/d)')
@click.option('--all', '-a', is_flag=True, help='Show all tasks including done')
def task_list(project, status, all):
    """List all tasks."""
    project_id = None

    if project:
        proj = db.get_project(project)
        if not proj:
            console.print(f"[red]✗[/red] Project '{project}' not found.")
            return
        project_id = proj['id']

    # Normalize status shortcut to full name
    if status:
        status = normalize_status(status)
        if status not in VALID_STATUSES:
            console.print(f"[red]✗[/red] Invalid status. Use: todo/t, in-progress/i, done/d")
            return

    # If status is explicitly provided, use it
    # Otherwise, if --all flag is not set, exclude done tasks
    if status is None and not all:
        # Get all tasks and filter out done ones
        all_tasks = db.list_tasks(project_id, None)
        tasks = [t for t in all_tasks if t['status'] != 'done']
    else:
        tasks = db.list_tasks(project_id, status)

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Sort tasks in reverse order by ID (newest first)
    tasks = sorted(tasks, key=lambda t: t['id'], reverse=True)

    table = Table(title="Tasks", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Title", style="white")
    table.add_column("Project", style="green")
    table.add_column("Status", width=12)
    table.add_column("Created", style="dim")

    for t in tasks:
        table.add_row(
            str(t['id']),
            t['title'],
            t['project_name'] or '-',
            format_status(t['status']),
            format_datetime(t['created_at'])
        )

    console.print(table)

@task.command('show')
@click.argument('task_id', type=int)
def task_show(task_id):
    """Show detailed information about a task."""
    task = db.get_task(task_id)

    if not task:
        console.print(f"[red]✗[/red] Task {task_id} not found.")
        return

    content = f"""[bold]ID:[/bold] {task['id']}
[bold]Title:[/bold] {task['title']}
[bold]Project:[/bold] {task['project_name'] or '-'}
[bold]Status:[/bold] {task['status']}
[bold]Description:[/bold] {task['description'] or '-'}
[bold]Created:[/bold] {format_datetime(task['created_at'])}
[bold]Updated:[/bold] {format_datetime(task['updated_at'])}"""

    console.print(Panel(content, title=f"Task #{task_id}", border_style="blue"))

@task.command('update')
@click.argument('task_id', type=int)
@click.option('--status', '-s', help='Update status (todo/t, in-progress/i, done/d)')
@click.option('--title', '-t', help='Update title')
@click.option('--description', '-d', help='Update description')
@click.option('--project', '-p', help='Update project')
def task_update(task_id, status, title, description, project):
    """Update a task."""
    task = db.get_task(task_id)
    if not task:
        console.print(f"[red]✗[/red] Task {task_id} not found.")
        return

    if status:
        # Normalize status shortcut to full name
        status = normalize_status(status)
        if status not in VALID_STATUSES:
            console.print(f"[red]✗[/red] Invalid status. Use: todo/t, in-progress/i, done/d")
            return

        if db.update_task_status(task_id, status):
            console.print(f"[green]✓[/green] Updated task {task_id} status to '{status}'")
        else:
            console.print(f"[red]✗[/red] Failed to update task {task_id}")

    project_id = None
    if project:
        proj = db.get_project(project)
        if not proj:
            console.print(f"[red]✗[/red] Project '{project}' not found.")
            return
        project_id = proj['id']

    if title or description or project_id:
        if db.update_task(task_id, title, description, project_id):
            console.print(f"[green]✓[/green] Updated task {task_id}")
        else:
            console.print(f"[red]✗[/red] Failed to update task {task_id}")

@task.command('delete')
@click.argument('task_id', type=int)
@click.confirmation_option(prompt='Are you sure you want to delete this task?')
def task_delete(task_id):
    """Delete a task."""
    if db.delete_task(task_id):
        console.print(f"[green]✓[/green] Deleted task {task_id}")
    else:
        console.print(f"[red]✗[/red] Task {task_id} not found.")

# Convenience commands
@cli.command('add')
@click.argument('title')
@click.option('--project', '-p', help='Project name')
@click.option('--description', '-d', help='Task description')
def add(title, project, description):
    """Quick command to add a task (alias for 'task create')."""
    ctx = click.get_current_context()
    ctx.invoke(task_create, title=title, project=project, description=description)

@cli.command('ls')
@click.option('--project', '-p', help='Filter by project name')
@click.option('--status', '-s', help='Filter by status (todo/t, in-progress/i, done/d)')
@click.option('--all', '-a', is_flag=True, help='Show all tasks including done')
def ls(project, status, all):
    """Quick command to list tasks (alias for 'task list')."""
    ctx = click.get_current_context()
    ctx.invoke(task_list, project=project, status=status, all=all)

@cli.command('done')
@click.argument('task_id', type=int)
def done(task_id):
    """Quick command to mark a task as done."""
    ctx = click.get_current_context()
    ctx.invoke(task_update, task_id=task_id, status='done', title=None, description=None, project=None)

@cli.command('purge')
@click.confirmation_option(prompt='Are you sure you want to delete ALL tasks and projects? This cannot be undone!')
def purge():
    """Delete all tasks and projects from the database."""
    try:
        db.purge_database()
        console.print("[green]✓[/green] Database purged successfully. All tasks and projects have been deleted.")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")

if __name__ == '__main__':
    cli()
