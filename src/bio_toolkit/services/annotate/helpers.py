from __future__ import annotations

from bio_toolkit.services.analyze.helpers import load_analysis_input
from bio_toolkit.services.analyze.request import AnalyzeRequest

from .request import AnnotateRequest


def load_annotation_input(request: AnnotateRequest, *, settings):
    return load_analysis_input(
        AnalyzeRequest(
            target=request.target,
            source=request.source,
            input_format=request.input_format,
            database=request.database,
            rettype=request.rettype,
        ),
        settings=settings,
    )
