# RAGA CLI
import typer

app = typer.Typer(
    name="raga",
    help="Ask the system anything — run bare to open the TUI, or use subcommands.",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Launch the TUI when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from tui.app import RagaApp
        RagaApp().run()


@app.command()
def status():
    """Show daemon health and index status."""
    from core.status_engine import get_status

    s = get_status()
    typer.echo(f"Watched dirs:   {', '.join(s['watched_dirs'])}")
    typer.echo(f"Files indexed:  {s['files_indexed']}")
    typer.echo(f"Files failed:   {s['files_failed']}")
    typer.echo(f"Last indexed:   {s['last_indexed_at'] or 'never'}")


@app.command()
def ask(query: str):
    """Ask a one-shot question."""
    from core.engine import ask as core_ask

    result = core_ask(query)
    typer.echo(result["text"])

    if result["sources"]:
        typer.echo("\nSources:")
        for path in result["sources"]:
            typer.echo(f"  {path}")


@app.command()
def reindex(path: str):
    """Force re-indexing of a directory."""
    import asyncio
    from core.reindex_engine import reindex_directory

    typer.echo(f"Indexing {path} ...")
    result = asyncio.run(reindex_directory(path))

    if "error" in result:
        typer.echo(f"Error: {result['error']}")
        raise typer.Exit(code=1)

    typer.echo(f"Done — {result['processed']}/{result['total_files']} files processed.")


@app.command()
def chat():
    """Launch TUI"""
    typer.echo("not implemented yet")


if __name__ == "__main__":
    app()