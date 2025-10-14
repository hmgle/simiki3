"""Command line interface for the Simiki Python 3 rewrite."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .build import build_site
from .config import ConfigError, ConfigFiles, default_config, load_config
from .content import PageError
from .migration import analyse_site, apply_fixes
from .page_scaffold import PageExistsError, create_page
from .scaffold import initialise_site
from .serve import PreviewServer
from .theme import ThemeError, builtin_themes, sync_theme_to_site
from .watch import BuildWatcher

app = typer.Typer(help="Static wiki generator rewritten for Python 3.")
console = Console()
theme_app = typer.Typer(help="Manage themes bundled with Simiki3.")
app.add_typer(theme_app, name="theme")
migration_app = typer.Typer(help="Migration helpers for legacy Simiki wikis.")
app.add_typer(migration_app, name="migrate")


def _project_root(path: Optional[Path]) -> Path:
    if path is None:
        return Path.cwd()
    return Path(path).expanduser().resolve()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, version: bool = typer.Option(  # pragma: no cover - delegated behaviour
    False,
    "--version",
    "-V",
    help="Show the simiki3 version and exit.",
)) -> None:
    """Entry point to display contextual help or the version."""
    if version:
        console.print(f"simiki3 {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
def init(
    path: Optional[Path] = typer.Argument(None, help="Target directory for the new wiki site."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files if they already exist."),
    title: Optional[str] = typer.Option(None, "--title", help="Site title written to _config.yml."),
    url: Optional[str] = typer.Option(None, "--url", help="Public URL of the wiki (trimmed automatically)."),
    root: Optional[str] = typer.Option(None, "--root", help="Root prefix for generated links (must start with '/')."),
) -> None:
    """Initialize a new wiki skeleton."""

    target = _project_root(path)
    overrides = {k: v for k, v in {"title": title, "url": url, "root": root}.items() if v is not None}

    try:
        base_config = default_config()
        config = base_config.with_overrides(**overrides) if overrides else base_config
    except ConfigError as exc:
        console.print(f"[red]Invalid configuration overrides[/red]: {exc}")
        raise typer.Exit(1)

    try:
        result = initialise_site(target, config=config, force=force)
    except (FileExistsError, NotADirectoryError) as exc:
        console.print(f"[red]Error[/red]: {exc}")
        raise typer.Exit(1)

    console.print(f"[green]Initialized wiki at[/green] {target}")

    if result.created_dirs:
        dirs_table = Table(title="Created directories")
        dirs_table.add_column("Path", style="cyan")
        for rel in sorted(result.created_dirs):
            dirs_table.add_row(rel)
        console.print(dirs_table)

    if result.created_files:
        files_table = Table(title="Created files")
        files_table.add_column("Path", style="green")
        for rel in sorted(result.created_files):
            files_table.add_row(rel)
        console.print(files_table)

    if result.skipped:
        skipped_table = Table(title="Skipped (already existed)")
        skipped_table.add_column("Path", style="yellow")
        for rel in sorted(result.skipped):
            skipped_table.add_row(rel)
        console.print(skipped_table)

    console.print(
        "Run [bold]simiki3 build[/bold] inside the site directory to render your wiki."
    )


@app.command()
def new(
    title: str = typer.Argument(..., help="Title for the new page."),
    path: Optional[Path] = typer.Option(None, "--path", help="Path to the wiki (defaults to current directory)."),
    category: str = typer.Option("intro", "--category", "-c", help="Category (relative to content directory)."),
    slug: Optional[str] = typer.Option(None, "--slug", "-s", help="Explicit slug/filename without extension."),
    draft: bool = typer.Option(False, "--draft", help="Mark the page as draft in its metadata."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite the page if it already exists."),
) -> None:
    """Create a new wiki page."""

    target = _project_root(path)
    try:
        config = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)

    try:
        result = create_page(
            target,
            config,
            title=title,
            category=category,
            slug=slug,
            draft=draft,
            force=force,
        )
    except PageExistsError as exc:
        console.print(f"[red]Page exists[/red]: {exc}")
        raise typer.Exit(1)

    rel_path = result.path.relative_to(target)
    console.print(
        f"[green]Created[/green] {rel_path} (slug: {result.slug})"
        + (" [draft]" if draft else "")
    )


@app.command()
def build(
    path: Optional[Path] = typer.Argument(None, help="Path to an existing wiki (defaults to current directory)."),
    include_drafts: bool = typer.Option(False, "--include-drafts", help="Include pages marked as draft metadata."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch source files and rebuild automatically (coming soon)."),
) -> None:
    """Build static HTML output from content."""

    if watch:
        console.print("[yellow]Watch mode is not yet implemented; building once.[/yellow]")

    target = _project_root(path)
    try:
        config = load_config(ConfigFiles().resolve(target))
    except FileNotFoundError as exc:
        console.print(f"[red]Configuration not found[/red]: {exc}")
        raise typer.Exit(1)
    except ConfigError as exc:
        console.print(f"[red]Invalid configuration[/red]: {exc}")
        raise typer.Exit(1)

    try:
        result = build_site(target, include_drafts=include_drafts, config=config)
    except ThemeError as exc:
        console.print(f"[red]Theme error[/red]: {exc}")
        raise typer.Exit(1)
    except PageError as exc:
        console.print(f"[red]Page error[/red]: {exc}")
        raise typer.Exit(1)

    console.print(
        f"[green]Build complete[/green]: rendered {len(result.rendered)} pages"
        f" (skipped {len(result.skipped)} drafts, copied {len(result.copied_assets)} assets)."
    )

    extras: list[str] = []
    if result.generated_catalog:
        extras.append("catalog")
    if result.generated_feed:
        extras.append("atom feed")
    if extras:
        console.print("Generated " + ", ".join(extras) + ".")

    if result.rendered:
        files_table = Table(title="Rendered pages")
        files_table.add_column("Path", style="green")
        for rel in sorted(str(p) for p in result.rendered):
            files_table.add_row(rel)
        console.print(files_table)

    if result.skipped:
        skip_table = Table(title="Skipped pages")
        skip_table.add_column("Path", style="yellow")
        for rel in sorted(str(p) for p in result.skipped):
            skip_table.add_row(rel)
        console.print(skip_table)


@theme_app.command("list")
def theme_list() -> None:
    """List built-in themes provided by Simiki3."""

    themes = builtin_themes()
    if not themes:
        console.print("No bundled themes available.")
        return

    table = Table(title="Available Themes")
    table.add_column("Name", style="cyan")
    for name in themes:
        table.add_row(name)
    console.print(table)


@theme_app.command("sync")
def theme_sync

@app.command()
def update(
    path: Optional[Path] = typer.Argument(None, help="Path to the wiki (defaults to current directory)."),
    overwrite: bool = typer.Option(False, "--overwrite", "-f", help="Overwrite existing files when syncing templates."),
    include_examples: bool = typer.Option(False, "--examples", help="Copy example content (getting started guides)."),
    sync_theme: bool = typer.Option(True, "--theme/--no-theme", help="Ensure the configured theme assets are present."),
) -> None:
    """Synchronise bundled configuration templates and theme assets."""

    target = _project_root(path)

    try:
        config = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)

    result = update_site(
        target,
        overwrite=overwrite,
        include_examples=include_examples,
        sync_theme=sync_theme,
        config=config,
    )

    def _print(title: str, items: list[Path], style: str) -> None:
        if not items:
            return
        table = Table(title=title)
        table.add_column("Path", style=style)
        for item in sorted(str(p) for p in items):
            table.add_row(item)
        console.print(table)

    _print("Copied files", result.copied_files, "green")
    _print("Skipped files", result.skipped_files, "yellow")

    if sync_theme:
        available = builtin_themes()
        if config.theme in result.theme_synced:
            console.print(
                f"[green]Synced theme[/green] '{config.theme}' into {config.themes_dir}/{config.theme}"
            )
        elif config.theme not in available:
            console.print(
                f"[yellow]Theme '{config.theme}' is not bundled with simiki3; consider porting it manually."
            )
        else:
            console.print("[green]Theme assets already present; no sync needed.")

    console.print("[green]Update tasks completed.")


@app.command()
def validate(
    legacy: Path = typer.Argument(..., help="Directory containing the legacy (Simiki) build output."),
    new: Path = typer.Argument(..., help="Directory containing the simiki3 build output."),
    extensions: str = typer.Option('html', '--ext', '-e', help="Comma-separated list of file extensions to compare."),
) -> None:
    """Compare legacy and simiki3 builds and report differences."""

    exts = [ext.strip() for ext in extensions.split(',') if ext.strip()] or None
    result = compare_directories(legacy, new, extensions=exts)

    def _render_table(title: str, items: list[Path], style: str) -> None:
        if not items:
            return
        table = Table(title=title)
        table.add_column('Path', style=style)
        for item in items:
            table.add_row(str(item))
        console.print(table)

    _render_table('Missing in new build', result.missing_in_new, 'red')
    _render_table('Missing in legacy build', result.missing_in_legacy, 'yellow')
    _render_table('Changed files', result.changed_files, 'cyan')

    if result.diffs:
        for path, diff_text in result.diffs.items():
            if diff_text:
                console.print(Panel(diff_text, title=str(path), subtitle='Unified diff', expand=False))

    if result.is_clean:
        console.print('[green]Build outputs match for selected files.[/green]')
    else:
        console.print('[red]Differences detected. Review the tables above.[/red]')
        raise typer.Exit(1)
(
    theme: Optional[str] = typer.Argument(None, help="Theme name to copy (defaults to the site's configured theme)."),
    path: Optional[Path] = typer.Option(None, "--path", help="Path to the wiki (defaults to current directory)."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files when syncing."),
) -> None:
    """Copy a bundled theme into the site's theme directory."""

    target = _project_root(path)
    try:
        config = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)

    theme_name = theme or config.theme
    try:
        result = sync_theme_to_site(target, config, theme_name, force=force)
    except ThemeError as exc:
        console.print(f"[red]Theme error[/red]: {exc}")
        raise typer.Exit(1)

    console.print(f"[green]Synced theme[/green] '{theme_name}' into {config.themes_dir}/{theme_name}")

    def _print_paths(title: str, paths: list[Path], style: str) -> None:
        if not paths:
            return
        table = Table(title=title)
        table.add_column("Path", style=style)
        for rel in sorted(str(p) for p in paths):
            table.add_row(rel)
        console.print(table)

    _print_paths("Created files", result.created, "green")
    _print_paths("Overwritten files", result.overwritten, "yellow")
    _print_paths("Skipped files", result.skipped, "red")


@migration_app.command("audit")
def migrate_audit(
    path: Optional[Path] = typer.Argument(None, help="Path to the legacy wiki (defaults to current directory)."),
) -> None:
    """Inspect a legacy Simiki site and report migration blockers."""

    target = _project_root(path)
    try:
        config = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)

    report = analyse_site(target, config)
    report.display(console)

    if report.has_blockers:
        console.print("[red]Blocking issues detected. Resolve them before migrating.[/red]")
        raise typer.Exit(1)

    if report.page_issues or report.config_warnings or report.theme_warnings:
        console.print("[yellow]Warnings detected. Review before proceeding with migration.[/yellow]")
    else:
        console.print("[green]Site is ready for simiki3 migration![/green]")


@migration_app.command("fix")
def migrate_fix(
    path: Optional[Path] = typer.Argument(None, help="Path to the legacy wiki (defaults to current directory)."),
    config: bool = typer.Option(True, "--config/--no-config", help="Rewrite _config.yml with normalised values."),
    pages: bool = typer.Option(True, "--pages/--no-pages", help="Update page front matter (layout, date)."),
    theme: bool = typer.Option(True, "--theme/--no-theme", help="Ensure the configured theme assets are synced."),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create .bak files before modifying content."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the fixes without modifying files."),
) -> None:
    """Apply automatic migration fixes to a legacy wiki."""

    if not config and not pages and not theme:
        console.print("[yellow]Nothing to do: enable --config, --pages, and/or --theme.[/yellow]")
        raise typer.Exit()

    target = _project_root(path)
    try:
        config_obj = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)

    summary = apply_fixes(
        target,
        config_obj,
        fix_config_file=config,
        fix_pages=pages,
        sync_theme=theme,
        backup=backup,
        dry_run=dry_run,
    )

    if config and summary.config_path:
        msg = "would update" if dry_run else "updated"
        console.print(f"[green]{msg.capitalize()}[/green] {summary.config_path.relative_to(target)}")

    if summary.page_actions:
        title = "Planned page updates" if dry_run else "Updated pages"
        table = Table(title=title)
        table.add_column("Page", style="cyan")
        table.add_column("Change", style="green")
        for action in summary.page_actions:
            table.add_row(str(action.path), action.description)
        console.print(table)
    else:
        console.print("[green]No page fixes required.[/green]")

    if theme:
        theme_dir = target / config_obj.themes_dir / config_obj.theme
        available = builtin_themes()
        if summary.theme_synced:
            status = "would sync" if dry_run else "synced"
            console.print(
                f"[green]{status.capitalize()} theme[/green] '{summary.theme_name}' into {config_obj.themes_dir}/{summary.theme_name}"
            )
        elif config_obj.theme not in available:
            console.print(
                f"[yellow]Theme '{config_obj.theme}' is not bundled with simiki3; migrate it manually.[/yellow]"
            )
        elif not theme_dir.exists():
            console.print(
                "[yellow]Theme assets not present; run without --dry-run to sync bundled theme.[/yellow]"
            )
        else:
            console.print("[green]Theme assets already present; no sync needed.[/green]")

    if dry_run:
        console.print("[yellow]Dry run complete. Re-run without --dry-run to apply changes.[/yellow]")
    else:
        console.print("[green]Migration fixes applied successfully.[/green]")


@app.command()
def serve(
    path: Optional[Path] = typer.Argument(None, help="Path to an existing wiki (defaults to current directory)."),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address for the preview server."),
    port: int = typer.Option(8000, "--port", help="Port for the preview server (0 for random)."),
    include_drafts: bool = typer.Option(False, "--include-drafts", help="Serve pages marked as draft."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Rebuild when files change."),
) -> None:
    """Serve the generated site locally."""

    target = _project_root(path)

    try:
        initial_result = build_site(target, include_drafts=include_drafts)
        config = load_config(ConfigFiles().resolve(target))
    except (FileNotFoundError, ConfigError) as exc:
        console.print(f"[red]Configuration error[/red]: {exc}")
        raise typer.Exit(1)
    except (ThemeError, PageError) as exc:
        console.print(f"[red]Build failed[/red]: {exc}")
        raise typer.Exit(1)

    console.print(
        f"[green]Initial build complete[/green]: rendered {len(initial_result.rendered)} pages"
        f" (skipped {len(initial_result.skipped)})"
    )

    output_dir = target / config.destination
    server = PreviewServer(directory=output_dir, host=host, port=port)
    server.start()
    console.print(
        f"Serving at http://{server.serve_host}:{server.serve_port}{config.root}/"
        " (press Ctrl+C to stop)"
    )

    watcher = None
    if watch:
        console.print("Watching for changes…")

        def on_rebuild(result, changes):
            change_summary = ", ".join(Path(changed).name for _, changed in changes)
            console.print(
                f"[cyan]Rebuilt[/cyan] ({len(result.rendered)} pages rendered, {len(result.skipped)} skipped)"
                + (f" due to {change_summary}" if change_summary else "")
            )

        def on_error(exc: Exception) -> None:
            console.print(f"[red]Build error during watch[/red]: {exc}")

        watcher = BuildWatcher(
            root=target,
            include_drafts=include_drafts,
            on_rebuild=on_rebuild,
            on_error=on_error,
        )
        watcher.start()

    try:
        server.wait()
    finally:
        if watcher is not None:
            watcher.stop()
    console.print("Server stopped.")


@app.command()
def goals() -> None:
    """Show the current roadmap milestones."""
    table = Table(title="simiki3 Roadmap")
    table.add_column("Milestone", style="cyan", justify="left")
    table.add_column("Description", style="green", justify="left")
    table.add_row("Baseline scaffolding", "Current phase: CLI skeleton and packaging setup")
    table.add_row("Site initialization", "Implement project generator and default theme embedding")
    table.add_row("Content pipeline", "Markdown rendering, template rendering, tagging, feeds")
    table.add_row("Preview & watch", "Run local server with incremental rebuilds")
    console.print(table)


if __name__ == "__main__":  # pragma: no cover - script entry point
    app()
