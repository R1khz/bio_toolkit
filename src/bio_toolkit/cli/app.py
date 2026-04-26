from __future__ import annotations

import typer

from .commands import (
    analyze,
    annotate,
    batch,
    blast,
    cache,
    compare,
    doctor,
    fetch,
    query,
    search,
    start,
    transform,
)
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
blast.register(app)
batch.register(app)
cache.register(app)
doctor.register(app)
start.register(app)
