"""RAGA CLI TYPER COMMANDS AND ENTRYPOINT"""
import typer 

app = typer.Typer(
    name = "raga",
    help = "Ask the system anything"
)

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
    