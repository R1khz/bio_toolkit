from __future__ import annotations

import typer

from bio_toolkit.services.doctor import DoctorRequest, run_doctor

from ..presenters.doctor_presenter import render_doctor_response
from .common import fail, get_console


def register(app: typer.Typer) -> None:
    @app.command()
    def doctor(
        ctx: typer.Context,
        create_dirs: bool = typer.Option(
            False, "--create-dirs", help="Create cache and output directories if missing."
        ),
    ) -> None:
        console = get_console(ctx)
        try:
            response = run_doctor(DoctorRequest(create_dirs=create_dirs))
        except Exception as exc:
            fail(console, str(exc))
            return

        render_doctor_response(console=console, response=response)
