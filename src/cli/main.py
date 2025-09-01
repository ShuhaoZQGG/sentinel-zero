"""Main CLI entry point for SentinelZero."""

import sys
import shlex
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
from ..utils.time_parser import parse_time_to_seconds, format_seconds_to_human

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
@click.option('--cmd', '-c', required=True, help='Command to execute (can include arguments)')
@click.option('--args', help='Additional command arguments as a single string')
@click.option('--dir', '-d', 'working_dir', help='Working directory')
@click.option('--env', '-e', multiple=True, help='Environment variables (KEY=VALUE)')
@click.option('--group', '-g', help='Process group name')
@click.option('--restart-policy', default='standard', help='Restart policy name')
@click.option('--restart-delay', help='Custom restart delay (e.g., 5h, 30m, 45s)')
@click.option('--schedule', help='Schedule expression (cron or interval)')
@click.option('--detach', is_flag=True, help='Run in background')
def start(name, cmd, args, working_dir, env, group, restart_policy, restart_delay, schedule, detach):
    """Start a new process."""
    try:
        # Parse the command using shlex to handle quoted strings properly
        cmd_parts = shlex.split(cmd)
        if not cmd_parts:
            raise ValueError("Command cannot be empty")
        
        actual_command = cmd_parts[0]
        actual_args = cmd_parts[1:]
        
        # If additional args are provided, parse and append them
        if args:
            additional_args = shlex.split(args)
            actual_args.extend(additional_args)
        
        # Parse environment variables
        env_vars = {}
        for e in env:
            if '=' in e:
                key, value = e.split('=', 1)
                env_vars[key] = value
        
        # Start the process
        info = process_manager.start_process(
            name=name,
            command=actual_command,
            args=actual_args,
            working_dir=working_dir,
            env_vars=env_vars,
            group=group
        )
        
        # Handle custom restart delay if provided
        if restart_delay:
            delay_seconds = parse_time_to_seconds(restart_delay)
            # Create a custom policy with the specified delay
            custom_policy_name = f"{name}-custom-delay"
            try:
                policy_manager.create_policy(
                    name=custom_policy_name,
                    retry_delay=int(delay_seconds),
                    max_retries=3,  # Default to 3 retries
                    backoff_multiplier=1.5
                )
                policy_manager.apply_policy(name, custom_policy_name)
            except ValueError:
                # Policy already exists, update it
                policy_manager.update_policy(
                    custom_policy_name,
                    retry_delay=int(delay_seconds)
                )
                policy_manager.apply_policy(name, custom_policy_name)
        else:
            # Apply standard restart policy
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
            # Check if process already exists and update it
            existing_process = session.query(ProcessModel).filter_by(name=name).first()
            if existing_process:
                existing_process.command = actual_command
                existing_process.args = actual_args
                existing_process.working_dir = working_dir
                existing_process.env_vars = env_vars
                existing_process.status = info.status.value
                existing_process.pid = info.pid
                existing_process.group_name = group
            else:
                process_model = ProcessModel(
                    name=name,
                    command=actual_command,
                    args=actual_args,
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
@click.option('--delay', '-d', help='Delay between stop and start (e.g., 30s, 5m, 1h)')
def restart(name, force, delay):
    """Restart a process."""
    try:
        # Parse delay if provided
        delay_seconds = 0
        if delay:
            delay_seconds = parse_time_to_seconds(delay)
        
        # If delay is specified, we need to stop first, wait, then start
        if delay_seconds > 0:
            # Stop the process
            process_manager.stop_process(name, force=force)
            console.print(f"[yellow]⏸[/yellow] Stopped process '{name}', waiting {format_seconds_to_human(delay_seconds)}...")
            
            # Wait for the specified delay
            import time
            time.sleep(delay_seconds)
            
            # Get the process info to restart with same config
            with get_session() as session:
                process_model = session.query(ProcessModel).filter_by(name=name).first()
                if process_model:
                    info = process_manager.start_process(
                        name=name,
                        command=process_model.command,
                        args=process_model.args or [],
                        working_dir=process_model.working_dir,
                        env_vars=process_model.env_vars or {},
                        group=process_model.group_name
                    )
                    console.print(f"[blue]🔄[/blue] Restarted process '{name}' (PID: {info.pid})")
                else:
                    console.print(f"[red]✗[/red] Process '{name}' not found in database")
                    sys.exit(1)
        else:
            # Regular restart without delay
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


@cli.group(name='restart-policy')
def restart_policy():
    """Manage restart policies."""
    pass


@restart_policy.command('create')
@click.option('--name', required=True, help='Policy name')
@click.option('--delay', help='Restart delay (e.g., 5h, 30m, 45s)')
@click.option('--max-retries', type=int, default=3, help='Maximum retry attempts')
@click.option('--backoff', type=float, default=1.5, help='Backoff multiplier')
@click.option('--max-delay', help='Maximum delay (e.g., 1h)')
def create_policy(name, delay, max_retries, backoff, max_delay):
    """Create a new restart policy."""
    try:
        # Parse delays if provided
        retry_delay = 5  # Default 5 seconds
        if delay:
            retry_delay = int(parse_time_to_seconds(delay))
        
        max_delay_seconds = 300  # Default 5 minutes
        if max_delay:
            max_delay_seconds = int(parse_time_to_seconds(max_delay))
        
        policy = policy_manager.create_policy(
            name=name,
            retry_delay=retry_delay,
            max_retries=max_retries,
            backoff_multiplier=backoff,
            max_delay=max_delay_seconds
        )
        
        console.print(f"[green]✓[/green] Created restart policy '{name}'")
        console.print(f"  Delay: {format_seconds_to_human(retry_delay)}")
        console.print(f"  Max retries: {max_retries}")
        console.print(f"  Backoff: {backoff}")
        console.print(f"  Max delay: {format_seconds_to_human(max_delay_seconds)}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@restart_policy.command('list')
def list_policies():
    """List all restart policies."""
    try:
        policies = policy_manager.list_policies()
        
        table = Table(title="Restart Policies")
        table.add_column("Name", style="cyan")
        table.add_column("Delay", style="green")
        table.add_column("Max Retries", style="yellow")
        table.add_column("Backoff", style="blue")
        table.add_column("Max Delay", style="magenta")
        
        for policy in policies:
            table.add_row(
                policy.name,
                format_seconds_to_human(policy.retry_delay),
                str(policy.max_retries),
                str(policy.backoff_multiplier),
                format_seconds_to_human(policy.max_delay)
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@restart_policy.command('update')
@click.argument('name')
@click.option('--delay', help='New restart delay (e.g., 5h, 30m, 45s)')
@click.option('--max-retries', type=int, help='New maximum retry attempts')
@click.option('--backoff', type=float, help='New backoff multiplier')
@click.option('--max-delay', help='New maximum delay (e.g., 1h)')
def update_policy(name, delay, max_retries, backoff, max_delay):
    """Update an existing restart policy."""
    try:
        kwargs = {}
        
        if delay:
            kwargs['retry_delay'] = int(parse_time_to_seconds(delay))
        if max_retries is not None:
            kwargs['max_retries'] = max_retries
        if backoff is not None:
            kwargs['backoff_multiplier'] = backoff
        if max_delay:
            kwargs['max_delay'] = int(parse_time_to_seconds(max_delay))
        
        if not kwargs:
            console.print("[yellow]No updates specified[/yellow]")
            return
        
        policy = policy_manager.update_policy(name, **kwargs)
        
        console.print(f"[green]✓[/green] Updated restart policy '{name}'")
        console.print(f"  Delay: {format_seconds_to_human(policy.retry_delay)}")
        console.print(f"  Max retries: {policy.max_retries}")
        console.print(f"  Backoff: {policy.backoff_multiplier}")
        console.print(f"  Max delay: {format_seconds_to_human(policy.max_delay)}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()