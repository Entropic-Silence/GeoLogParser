"""Explicit, testable SI unit conversion without discarding source units."""

from __future__ import annotations

from decimal import Decimal


METRES_PER_FOOT = Decimal("0.3048")


def feet_to_metres(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value)) * METRES_PER_FOOT


def metres_to_feet(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value)) / METRES_PER_FOOT

