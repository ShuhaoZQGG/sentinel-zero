"""Main CLI entry point for SentinelZero."""

import sys
import click
import structlog
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from ..core.process_manager import ProcessManager, ProcessStatus
from ..core.scheduler import ProcessScheduler, ScheduleType
from ..core.restart_policy import RestartPolicyManager
from ..models.base import init_db, get_session
from ..models.models import Process as ProcessModel

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

console = Console()

# Global instances
process_manager = ProcessManager()
scheduler = ProcessScheduler()
policy_manager = RestartPolicyManager()

# Connect scheduler to process manager
scheduler.set_process_manager(process_manager)

# Initialize database
init_db()


@click.group()
@click.option('--log-level', default='info', type=click.Choice(['debug', 'info', 'warn', 'error']))
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.version_option(version='0.1.0')
def cli(log_level, no_color):
    """SentinelZero - Process monitoring and management service."""
    if no_color:
        console.no_color = True


@cli.command()
@click.option('--name', '-n', required=True, help='Process name')
@click.option('--cmd', '-c', required=True, help='Command to execute')
@click.option('--args', multiple=True, help='Command arguments')
@click.option('--dir', '-d', 'working_dir', help='Working directory')
@click.option('--env', '-e', multiple=True, help='Environment variables (KEY=VALUE)')
@click.option('--group', '-g', help='Process group name')
@click.option('--restart-policy', default='standard', help='Restart policy name')
@click.option('--schedule', help='Schedule expression (cron or interval)')
@click.option('--detach', is_flag=True, help='Run in background')
def start(name, cmd, args, working_dir, env, group, restart_policy, schedule, detach):
    """Start a new process."""
    try:
        # Parse environment variables
        env_vars = {}
        for e in env:
            if '=' in e:
                key, value = e.split('=', 1)
                env_vars[key] = value
        
        # Start the process
        info = process_manager.start_process(
            name=name,
            command=cmd,
            args=list(args) if args else [],
            working_dir=working_dir,
            env_vars=env_vars,
            group=group
        )
        
        # Apply restart policy
        policy_manager.apply_policy(name, restart_policy)
        
        # Add schedule if provided
        if schedule:
            # Determine schedule type
            if schedule.startswith('@'):
                # Special cron syntax
                schedule_type = ScheduleType.CRON
                expression = schedule[1:]
            elif any(unit in schedule for unit in ['s', 'm', 'h', 'd']):
                schedule_type = ScheduleType.INTERVAL
                expression = schedule
            else:
                # Assume cron
                schedule_type = ScheduleType.CRON
                expression = schedule
            
            scheduler.add_schedule(
                name=f"{name}-schedule",
                schedule_type=schedule_type,
                expression=expression,
                command=cmd,
                args=list(args) if args else [],
                working_dir=working_dir,
                env_vars=env_vars
            )
        
        # Save to database
        with get_session() as session:
            process_model = ProcessModel(
                name=name,
                command=cmd,
                args=list(args) if args else [],
                working_dir=working_dir,
                env_vars=env_vars,
                status=info.status.value,
                pid=info.pid,
                group_name=group
            )
            session.add(process_model)
        
        console.print(f"[green]✓[/green] Started process '{name}' (PID: {info.pid})")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to start process: {e}")
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Force kill (SIGKILL)')
@click.option('--timeout', '-t', default=10, help='Grace period in seconds')
@click.option('--all', 'stop_all', is_flag=True, help='Stop all processes')
def stop(name, force, timeout, stop_all):
    """Stop a running process."""
    try:
        if stop_all:
            processes = process_manager.list_processes()
            for proc in processes:
                if proc.status == ProcessStatus.RUNNING:
                    process_manager.stop_process(proc.name, force=force, timeout=timeout)
                    console.print(f"[yellow]⏸[/yellow] Stopped process '{proc.name}'")
        else:
            result = process_manager.stop_process(name, force=force, timeout=timeout)
            if result:
                console.print(f"[yellow]⏸[/yellow] Stopped process '{name}'")
                
                # Update database
                with get_session() as session:
                    process_model = session.query(ProcessModel).filter_by(name=name).first()
                    if process_model:
                        process_model.status = "stopped"
                        process_model.pid = None
            else:
                console.print(f"[red]✗[/red] Failed to stop process '{name}'")
                sys.exit(1)
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Force restart')
@click.option('--delay', '-d', default=0, help='Delay between stop and start')
def restart(name, force, delay):
    """Restart a process."""
    try:
        info = process_manager.restart_process(name)
        console.print(f"[blue]🔄[/blue] Restarted process '{name}' (PID: {info.pid})")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('name', required=False)
@click.option('--watch', '-w', type=int, help='Auto-refresh every N seconds')
@click.option('--metrics', '-m', is_flag=True, help='Include resource metrics')
@click.option('--history', is_flag=True, help='Show status history')
def status(name, watch, metrics, history):
    """Show process status."""
    try:
        if name:
            # Show specific process
            info = process_manager.get_process_info(name)
            if not info:
                console.print(f"[red]✗[/red] Process '{name}' not found")
                sys.exit(1)
            
            # Create status panel
            status_color = {
                ProcessStatus.RUNNING: "green",
                ProcessStatus.STOPPED: "yellow",
                ProcessStatus.FAILED: "red",
                ProcessStatus.STARTING: "blue",
                ProcessStatus.STOPPING: "orange"
            }.get(info.status, "white")
            
            panel_content = f"""
[bold]Name:[/bold] {info.name}
[bold]Status:[/bold] [{status_color}]{info.status.value}[/{status_color}]
[bold]Command:[/bold] {info.command} {' '.join(info.args)}
[bold]PID:[/bold] {info.pid or '-'}
[bold]Working Dir:[/bold] {info.working_dir or '-'}
[bold]Group:[/bold] {info.group or '-'}
[bold]Restart Count:[/bold] {info.restart_count}
"""
            
            if metrics and info.status == ProcessStatus.RUNNING:
                metrics_data = process_manager.get_process_metrics(name)
                if metrics_data:
                    panel_content += f"""
[bold]CPU:[/bold] {metrics_data['cpu_percent']}%
[bold]Memory:[/bold] {metrics_data['memory_mb']} MB
[bold]Threads:[/bold] {metrics_data['num_threads']}
"""
            
            console.print(Panel(panel_content.strip(), title=f"Process: {name}"))
            
        else:
            # Show all processes
            processes = process_manager.list_processes()
            
            table = Table(title="Process Status")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("PID", style="magenta")
            table.add_column("CPU%", style="green")
            table.add_column("Memory", style="yellow")
            table.add_column("Uptime", style="blue")
            
            for proc in processes:
                status_icon = {
                    ProcessStatus.RUNNING: "🟢",
                    ProcessStatus.STOPPED: "🟡",
                    ProcessStatus.FAILED: "🔴",
                    ProcessStatus.STARTING: "🔵",
                    ProcessStatus.STOPPING: "🟠"
                }.get(proc.status, "⚪")
                
                cpu = "-"
                memory = "-"
                
                if metrics and proc.status == ProcessStatus.RUNNING:
                    metrics_data = process_manager.get_process_metrics(proc.name)
                    if metrics_data:
                        cpu = f"{metrics_data['cpu_percent']}%"
                        memory = f"{metrics_data['memory_mb']} MB"
                
                uptime = "-"
                if proc.started_at:
                    from datetime import datetime
                    delta = datetime.now() - proc.started_at
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    if delta.days > 0:
                        uptime = f"{delta.days}d {hours}h"
                    elif hours > 0:
                        uptime = f"{hours}h {minutes}m"
                    else:
                        uptime = f"{minutes}m"
                
                table.add_row(
                    proc.name,
                    f"{status_icon} {proc.status.value}",
                    str(proc.pid) if proc.pid else "-",
                    cpu,
                    memory,
                    uptime
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--filter', '-f', 'filter_by', help='Filter by status/group')
@click.option('--sort', '-s', help='Sort by field')
@click.option('--limit', '-l', type=int, help='Limit results')
def list(filter_by, sort, limit):
    """List all processes."""
    try:
        processes = process_manager.list_processes()
        
        # Apply filters
        if filter_by:
            if '=' in filter_by:
                key, value = filter_by.split('=', 1)
                if key == 'status':
                    processes = [p for p in processes if p.status.value == value]
                elif key == 'group':
                    processes = [p for p in processes if p.group == value]
        
        # Apply sorting
        if sort:
            reverse = sort.startswith('-')
            sort_key = sort.lstrip('-')
            processes.sort(key=lambda p: getattr(p, sort_key, ''), reverse=reverse)
        
        # Apply limit
        if limit:
            processes = processes[:limit]
        
        # Display table
        table = Table(title="Processes")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Command", style="green")
        table.add_column("Last Started", style="blue")
        table.add_column("Restart Count", style="yellow")
        
        for proc in processes:
            last_started = "-"
            if proc.started_at:
                last_started = proc.started_at.strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(
                proc.name,
                proc.status.value,
                f"{proc.command} {' '.join(proc.args)}",
                last_started,
                str(proc.restart_count)
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--tail', '-t', type=int, default=100, help='Number of lines to show')
@click.option('--since', help='Show logs since timestamp')
@click.option('--level', help='Filter by log level')
@click.option('--grep', help='Filter by pattern')
def logs(name, follow, tail, since, level, grep):
    """View process logs."""
    try:
        output = process_manager.get_process_output(name)
        
        if not output:
            console.print(f"[yellow]No logs available for process '{name}'[/yellow]")
            return
        
        # Display stdout
        if output.get('stdout'):
            console.print("[bold cyan]STDOUT:[/bold cyan]")
            lines = output['stdout'].splitlines()
            if tail:
                lines = lines[-tail:]
            for line in lines:
                if not grep or grep in line:
                    console.print(line)
        
        # Display stderr
        if output.get('stderr'):
            console.print("\n[bold red]STDERR:[/bold red]")
            lines = output['stderr'].splitlines()
            if tail:
                lines = lines[-tail:]
            for line in lines:
                if not grep or grep in line:
                    console.print(line)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()