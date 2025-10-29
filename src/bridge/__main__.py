"""
Project entrypoint exposing both a CLI and an API runner.
"""

import typer
import uvicorn

from bridge.adapters import cli_app

main_app = typer.Typer(help="GitHub ⇄ bio.tools bridge entrypoint")

# attach cli app as a subcommand
main_app.add_typer(cli_app, name="cli", help="Run the Bridge CLI interface")


@main_app.command("api")
def run_api(
    host: str = typer.Option("localhost", "--host", help="API host address"),
    port: int = typer.Option(8000, "--port", help="API port"),
    reload: bool = typer.Option(True, "--reload", help="Enable hot reload"),
):
    """Run the FastAPI web service."""
    # uvicorn.run(api_app, host=host, port=port, reload=reload)
    print(f"Access Swagger UI at http://{host}:{port}/docs")
    uvicorn.run("bridge.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main_app()
