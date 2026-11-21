"""Load and validate editable calculator rates."""

import json
from decimal import Decimal
from importlib.resources import files

from pydantic import BaseModel


class RateTier(BaseModel):
    """A unit price valid up to a production quantity."""

    max_quantity: int | None
    price: Decimal


class BusinessCardRates(BaseModel):
    """Fixed prices for supported business-card runs."""

    prices: dict[str, dict[str, dict[int, Decimal]]]


class DigitalRates(BaseModel):
    """Per-sheet digital print prices and finishing."""

    prices: dict[str, dict[str, list[RateTier]]]
    formats_up: dict[str, int]
    cutting: Decimal
    saddle_stitch: Decimal


class BannerMaterial(BaseModel):
    """Large-format roll material configuration."""

    label: str
    max_width_mm: int
    price_per_linear_metre: Decimal


class BannerRates(BaseModel):
    """Large-format print and finishing rates."""

    materials: dict[str, BannerMaterial]
    waste_percent: Decimal
    hemming_per_metre: Decimal
    eyelet: Decimal


class Rates(BaseModel):
    """Complete versioned rate card."""

    version: str
    currency: str
    vat_percent: Decimal
    minimum_order: Decimal
    business_cards: BusinessCardRates
    digital_print: DigitalRates
    banners: BannerRates


def load_rates() -> Rates:
    """Read the bundled rate card and validate its schema."""
    path = files("printcalc").joinpath("rates.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Rates.model_validate(raw)
