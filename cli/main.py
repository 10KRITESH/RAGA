"""RAGA CLI TYPER COMMANDS AND ENTRYPOINT"""
import typer 

app = typer.Typer(
    name = "raga",
    help = "Ask the system anything"
)

@app.command()
def status():
    """Show daemon health and index status."""
    typer.echo("not implemented yet")

@app.command()
def ask(query: str):
    """Ask a Question."""
    typer.echo("not implemented yet")

@app.command()
def reindex(path: str):
    """Force re-indexing of a directory."""
    typer.echo("not implemented yet")

@app.command()
def chat():
    """Launch TUI"""
    typer.echo("not implemented yet")

if __name__ == "__main__":
    app()
    