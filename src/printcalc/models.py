"""Domain models for quote requests and results."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class ProductType(StrEnum):
    """Products supported by the MVP."""

    BUSINESS_CARDS = "business_cards"
    FLYERS = "flyers"
    BROCHURES = "brochures"
    BANNERS = "banners"


class QuoteRequest(BaseModel):
    """Normalized calculator input."""

    product_type: ProductType
    quantity: int = Field(gt=0, le=100_000)
    format: str = "A5"
    material: str = "smooth"
    sides: int = Field(default=1, ge=1, le=2)
    pages: int = Field(default=4, ge=4, le=500)
    width_mm: int = Field(default=1000, gt=0, le=10_000)
    height_mm: int = Field(default=1000, gt=0, le=100_000)
    cutting: bool = False
    hemming: bool = False
    eyelets: int = Field(default=0, ge=0, le=1_000)
    markup_percent: Decimal = Field(default=Decimal(20), ge=0, le=500)
    include_vat: bool = False


class QuoteLine(BaseModel):
    """One explainable part of a quote."""

    label: str
    amount: Decimal


class Quote(BaseModel):
    """Calculated price with an audit-friendly breakdown."""

    product_type: ProductType
    quantity: int
    production_units: Decimal
    lines: list[QuoteLine]
    base_cost: Decimal
    markup: Decimal
    vat: Decimal
    total: Decimal
    unit_price: Decimal
    minimum_order_applied: bool
