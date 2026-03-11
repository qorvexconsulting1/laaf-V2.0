"""
LAAF CLI — Command-line interface for the Logic-layer Automated Attack Framework.

Commands:
  laaf scan            Run a PSB scan against a target LLM platform
  laaf serve           Start the REST API + web dashboard server
  laaf report          Generate a report from existing results
  laaf list-techniques Show all 49 taxonomy techniques
  laaf validate-config Validate a YAML config file
"""

from __future__ import annotations

import asyncio
import sys

# Force UTF-8 output on Windows so Rich can render Unicode characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import uuid
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import print as rprint

import laaf
from laaf.taxonomy.base import Category, get_registry

console = Console(force_terminal=True)

_BANNER = (
    "\n"
    "[bold blue]  LAAF - Logic-layer Automated Attack Framework[/bold blue]\n"
    f"[dim]  v{laaf.__version__} | Atta et al., Qorvex Research, 2026 | arXiv:2507.10457[/dim]\n"
)


@click.group()
@click.version_option(laaf.__version__, prog_name="laaf")
def cli():
    """LAAF — Enterprise LPCI Red-Teaming Framework for Agentic LLM Systems."""
    pass


# ── laaf scan ────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--target", "-t", required=True,
              type=click.Choice(["openai", "anthropic", "google", "huggingface", "azure", "openrouter", "mock"], case_sensitive=False),
              help="Target LLM platform")
@click.option("--model", "-m", default=None, help="Model override (e.g. gpt-4o)")
@click.option("--stages", "-s", default="all",
              help="Comma-separated stage IDs to test (e.g. S1,S3,S5) or 'all'")
@click.option("--payloads", "-p", default=100, show_default=True,
              help="Max payloads per stage")
@click.option("--output", "-o", default="results", show_default=True,
              help="Output directory")
@click.option("--format", "-f", "fmt", default="csv,html",
              help="Report format(s): csv,json,html,pdf (comma-separated)")
@click.option("--rate-delay", default=2.0, show_default=True,
              help="Seconds between requests")
@click.option("--config-dir", default=None, type=click.Path(exists=True),
              help="Path to configs/ directory for stage context overrides")
@click.option("--dry-run", is_flag=True, help="Generate payloads without sending to LLM")
@click.option("--scan-id", default=None, help="Custom scan ID (auto-generated if omitted)")
@click.option("--exfil-url", default=None,
              help="Attacker callback URL for data exfiltration PoC (activates EX1-EX5 techniques). "
                   "Use a webhook.site URL or ngrok endpoint to capture exfiltrated data.")
def scan(target, model, stages, payloads, output, fmt, rate_delay, config_dir, dry_run, scan_id, exfil_url):
    """Run a Persistent Stage Breaker scan against a target LLM platform."""
    console.print(_BANNER)

    scan_id = scan_id or f"laaf-{target}-{uuid.uuid4().hex[:8]}"
    output_dir = Path(output) / scan_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve stages
    if stages.lower() == "all":
        stage_list = ["S1", "S2", "S3", "S4", "S5", "S6"]
    else:
        stage_list = [s.strip().upper() for s in stages.split(",")]

    exfil_note = f"\n[bold]Exfil URL:[/bold] {exfil_url}" if exfil_url else ""
    console.print(Panel(
        f"[bold]Scan ID:[/bold] {scan_id}\n"
        f"[bold]Target:[/bold] {target.upper()}\n"
        f"[bold]Stages:[/bold] {', '.join(stage_list)}\n"
        f"[bold]Max payloads/stage:[/bold] {payloads}\n"
        f"[bold]Output:[/bold] {output_dir}\n"
        f"[bold]Dry run:[/bold] {'YES' if dry_run else 'NO'}"
        + exfil_note,
        title="[bold blue]LAAF Scan Configuration[/bold blue]",
        border_style="blue",
    ))
    if exfil_url:
        console.print(
            f"[yellow]Exfiltration mode:[/yellow] EX1-EX5 techniques active. "
            f"Monitor your callback URL for incoming data.\n"
        )

    if dry_run:
        _dry_run_demo(stage_list, payloads)
        return

    asyncio.run(_run_scan(
        target=target,
        model=model,
        stage_list=stage_list,
        max_payloads=payloads,
        output_dir=output_dir,
        scan_id=scan_id,
        rate_delay=rate_delay,
        config_dir=Path(config_dir) if config_dir else None,
        fmt=fmt,
        exfil_url=exfil_url,
    ))


async def _run_scan(target, model, stage_list, max_payloads, output_dir, scan_id,
                    rate_delay, config_dir, fmt, exfil_url=None):
    from laaf.core.engine import StageEngine
    from laaf.core.stage_breaker import PersistentStageBreaker
    from laaf.platforms import get_platform
    from laaf.reporting import get_reporter

    platform = get_platform(target, model=model)
    engine = StageEngine(config_dir=config_dir)
    stage_contexts = {sid: engine.get_context(sid) for sid in stage_list if engine.get_context(sid)}

    console.print(f"\n[cyan]Initialising platform:[/cyan] {platform}")

    progress_table: dict[str, dict] = {sid: {"attempts": 0, "outcome": "—"} for sid in stage_list}

    def on_progress(stage_id: str, attempt: int, outcome: str, confidence: float):
        progress_table[stage_id] = {"attempts": attempt, "outcome": outcome}

    psb = PersistentStageBreaker(
        platform=platform,
        stage_contexts=stage_contexts,
        max_attempts=max_payloads,
        rate_delay=rate_delay,
        progress_callback=on_progress,
        exfil_url=exfil_url,
    )

    console.print("\n[bold]Starting Persistent Stage Breaker...[/bold]\n")
    result = await psb.run(stages=stage_list)

    # Print results table
    table = Table(title="PSB Results", show_lines=True)
    table.add_column("Stage", style="bold")
    table.add_column("Status")
    table.add_column("Attempts", justify="right")
    table.add_column("Technique")
    table.add_column("Confidence", justify="right")
    table.add_column("Duration")

    for s in result.stages:
        status = "[red]BROKEN[/red]" if s.broken else "[green]RESISTANT[/green]"
        tech = s.winning_payload.technique_id if s.winning_payload else "—"
        table.add_row(
            s.stage_id, status, str(s.attempts), tech,
            f"{s.winning_confidence:.0%}", f"{s.duration_seconds:.1f}s",
        )
    console.print(table)

    console.print(
        f"\n[bold]Overall Breakthrough Rate:[/bold] "
        f"[{'red' if result.overall_breakthrough_rate > 0.3 else 'green'}]"
        f"{result.overall_breakthrough_rate:.0%}[/]\n"
    )

    # Generate reports
    for f in fmt.split(","):
        f = f.strip()
        try:
            reporter = get_reporter(f)
            out = reporter.generate(result, output_dir / f"report_{scan_id}")
            console.print(f"[dim]Report:[/dim] {out}")
        except Exception as exc:
            console.print(f"[yellow]Warning:[/yellow] Could not generate {f} report: {exc}")


def _dry_run_demo(stage_list: list[str], count: int) -> None:
    from laaf.generators.payload_generator import PayloadGenerator
    gen = PayloadGenerator(seed=42)
    payloads = gen.generate(count=min(count, 20))
    table = Table(title=f"Sample Payloads (dry-run, showing {len(payloads)})")
    table.add_column("ID")
    table.add_column("Technique")
    table.add_column("Category")
    table.add_column("Preview", max_width=60)
    for p in payloads:
        table.add_row(p.id, p.technique_id, p.category, p.content[:60] + "…")
    console.print(table)
    gen2 = PayloadGenerator()
    big_batch = gen2.generate(count=1000)
    console.print(f"\n[green]Payload space demo:[/green] Generated {len(big_batch):,} unique payloads "
                  f"(theoretical space: 500,000+)")


# ── laaf serve ───────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8080, show_default=True)
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
def serve(host, port, reload):
    """Start the LAAF REST API and web dashboard server."""
    console.print(_BANNER)
    console.print(f"[bold green]Starting LAAF server[/bold green] at http://{host}:{port}")
    console.print(f"  API docs:  http://{host}:{port}/docs")
    console.print(f"  Dashboard: http://{host}:{port}/dashboard\n")
    try:
        import uvicorn
        from laaf.api.server import create_app
        app = create_app()
        uvicorn.run(app, host=host, port=port, reload=reload)
    except ImportError:
        console.print("[red]uvicorn not installed. Run: pip install uvicorn[standard][/red]")
        sys.exit(1)


# ── laaf report ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True),
              help="Path to existing JSON results file")
@click.option("--format", "-f", "fmt", default="html",
              type=click.Choice(["csv", "json", "html", "pdf"], case_sensitive=False))
@click.option("--output", "-o", default=None, help="Output file path (auto-derived if omitted)")
def report(input_path, fmt, output):
    """Generate a report from an existing JSON results file."""
    import json as _json
    from laaf.reporting import get_reporter

    input_path = Path(input_path)
    out = Path(output) if output else input_path.with_suffix(f".{fmt}")

    try:
        with open(input_path) as f:
            data = _json.load(f)
        # Reconstruct minimal PSBResult for reporting
        from laaf.core.stage_breaker import PSBResult, StageResult
        from laaf.taxonomy.base import Outcome
        stages = []
        for s in data.get("stages", []):
            stages.append(StageResult(
                stage_id=s["stage_id"],
                stage_name=s["stage_name"],
                broken=s["broken"],
                attempts=s["attempts"],
                winning_payload=None,
                winning_outcome=Outcome.EXECUTED if s["broken"] else Outcome.BLOCKED,
                winning_confidence=s["confidence"],
                duration_seconds=s["duration_seconds"],
                all_outcomes=s.get("outcomes", {}),
            ))
        result = PSBResult(
            platform=data.get("platform", "unknown"),
            model=data.get("model", "unknown"),
            stages=stages,
            total_duration_seconds=data.get("total_duration_seconds", 0),
            total_attempts=data.get("total_attempts", 0),
        )
        reporter = get_reporter(fmt)
        out_path = reporter.generate(result, out)
        console.print(f"[green]Report generated:[/green] {out_path}")
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


# ── laaf list-techniques ──────────────────────────────────────────────────────

@cli.command("list-techniques")
@click.option("--category", "-c", default=None,
              type=click.Choice([c.value for c in Category], case_sensitive=False),
              help="Filter by category")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_techniques(category, as_json):
    """List all 49 LPCI attack techniques in the taxonomy."""
    import json as _json
    registry = get_registry()
    if category:
        techniques = registry.by_category(Category(category))
    else:
        techniques = registry.all()

    if as_json:
        data = [
            {"id": t.id, "name": t.name, "category": t.category.value,
             "lpci_stage": t.lpci_stage, "description": t.description,
             "tags": t.tags}
            for t in techniques
        ]
        click.echo(_json.dumps(data, indent=2))
        return

    table = Table(title=f"LAAF Technique Taxonomy ({len(techniques)} techniques)")
    table.add_column("ID", style="bold cyan", width=5)
    table.add_column("Category", width=12)
    table.add_column("Name", width=28)
    table.add_column("LPCI Stage", width=8)
    table.add_column("Description", max_width=55)

    category_colors = {
        "encoding": "green",
        "structural": "blue",
        "semantic": "magenta",
        "layered": "red",
        "trigger": "yellow",
    }

    from rich.markup import escape
    for t in techniques:
        color = category_colors.get(t.category.value, "white")
        table.add_row(
            t.id,
            f"[{color}]{t.category.value}[/{color}]",
            escape(t.name),
            t.lpci_stage,
            escape(t.description[:80]),
        )
    console.print(table)
    from laaf.generators.payload_generator import PayloadGenerator
    _space = PayloadGenerator().theoretical_payload_space
    console.print(f"\n[dim]Total: {len(techniques)} techniques | "
                  f"Theoretical payload space: {_space:,} | Practical: 500,000+[/dim]")


# ── laaf validate-config ──────────────────────────────────────────────────────

@cli.command("validate-config")
@click.argument("config_path", type=click.Path(exists=True))
def validate_config(config_path):
    """Validate a LAAF YAML configuration file."""
    import yaml
    from laaf.utils.validators import validate_yaml_config
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        validate_yaml_config(data)
        console.print(f"[green]✓ Valid config[/green] — {config_path}")
        console.print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
    except Exception as exc:
        console.print(f"[red]✗ Invalid config:[/red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
