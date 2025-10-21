from __future__ import annotations
from typing import Literal
from .base import BitPacking
from .crossing import BitPackingCrossing
from .aligned import BitPackingAligned
from .overflow import BitPackingOverflow

Kind = Literal["crossing", "aligned", "overflow"]

def create(kind: Kind, **opts) -> BitPacking:
    if kind == "crossing":
        return BitPackingCrossing(**opts)
    if kind == "aligned":
        return BitPackingAligned(**opts)
    if kind == "overflow":
        return BitPackingOverflow(**opts)
    raise ValueError(f"unknown kind: {kind}")
