from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from .pipeline import build_observatory
from .sources import download_onet_releases
from .taxonomy import TransparentSkillClassifier

app = typer.Typer(
    no_args_is_help=True,
    help="Build and inspect the AI Labor Observatory.",
)


@app.command()
def build(
    previous_dir: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    current_dir: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    output_dir: Annotated[Path, typer.Option()] = Path("data/sample"),
    occupation_limit: Annotated[int, typer.Option(min=40, max=250)] = 120,
    offline: Annotated[
        bool,
        typer.Option(help="Use only BLS observations already cached in the output directory."),
    ] = False,
) -> None:
    """Build all analytical artifacts from O*NET workbooks and the BLS API."""
    summary = build_observatory(
        previous_dir=previous_dir,
        current_dir=current_dir,
        output_dir=output_dir,
        occupation_limit=occupation_limit,
        offline=offline,
    )
    typer.echo(
        f"Built {summary['coverage']['wage_model_occupations']} wage-linked occupations "
        f"at {output_dir}"
    )


@app.command()
def classify(skill: str) -> None:
    """Show the transparent taxonomy prediction for a software skill."""
    prediction = TransparentSkillClassifier().predict_one(skill)
    typer.echo(json.dumps(prediction.as_dict(), indent=2))


@app.command("fetch-sources")
def fetch_sources(
    destination: Annotated[Path, typer.Option()] = Path("data/raw"),
) -> None:
    """Download and extract the two CC BY O*NET database releases."""
    releases = download_onet_releases(destination)
    for release, path in releases.items():
        typer.echo(f"O*NET {release}: {path}")


@app.command()
def serve(
    data_dir: Annotated[Path, typer.Option()] = Path("data/sample"),
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8000,
) -> None:
    """Serve the analytical API."""
    from .api import create_app

    uvicorn.run(create_app(data_dir), host=host, port=port)


if __name__ == "__main__":
    app()
