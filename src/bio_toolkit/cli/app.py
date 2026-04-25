from __future__ import annotations

import typer

from bio_toolkit.legacy_cli import (
    batch as legacy_batch,
)
from bio_toolkit.legacy_cli import (
    blast as legacy_blast,
)
from bio_toolkit.legacy_cli import (
    cache as legacy_cache,
)
from bio_toolkit.legacy_cli import (
    doctor as legacy_doctor,
)
from bio_toolkit.legacy_cli import (
    start as legacy_start,
)

from .commands import analyze, annotate, compare, fetch, query, search, transform
from .commands.common import register_root_callback

app = typer.Typer(
    add_completion=False,
    help="Linux-first CLI toolkit for NCBI sequence retrieval and analysis.",
    no_args_is_help=False,
)

register_root_callback(app)

search.register(app)
query.register(app)
fetch.register(app)
analyze.register(app)
annotate.register(app)
compare.register(app)
transform.register(app)

app.command(name="doctor")(legacy_doctor)
app.command(name="start")(legacy_start)
app.command(name="blast")(legacy_blast)
app.command(name="batch")(legacy_batch)
app.command(name="cache")(legacy_cache)
