from decimal import Decimal

import pytest

from printcalc.calculator import CalculationError, calculate_quote
from printcalc.models import ProductType, QuoteRequest
from printcalc.rates import Rates, load_rates


@pytest.fixture
def rates() -> Rates:
    return load_rates()


def test_business_cards_use_exact_public_price_tier(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.BUSINESS_CARDS,
        quantity=96,
        material="smooth",
        sides=2,
        markup_percent=0,
        include_vat=False,
    )

    quote = calculate_quote(request, rates)

    assert quote.base_cost == Decimal("360.00")
    assert quote.total == Decimal("360.00")
    assert quote.unit_price == Decimal("3.75")


def test_business_cards_reject_unsupported_quantity(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.BUSINESS_CARDS,
        quantity=100,
        material="smooth",
        sides=1,
    )

    with pytest.raises(CalculationError, match="тираж"):
        calculate_quote(request, rates)


def test_flyer_quote_includes_cutting_markup_and_vat(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.FLYERS,
        quantity=200,
        format="A5",
        material="160",
        sides=2,
        cutting=True,
        markup_percent=20,
        include_vat=True,
    )

    quote = calculate_quote(request, rates)

    assert quote.production_units == Decimal(50)
    assert quote.base_cost == Decimal("2150.00")
    assert quote.markup == Decimal("430.00")
    assert quote.vat == Decimal("516.00")
    assert quote.total == Decimal("3096.00")


def test_brochure_requires_page_count_divisible_by_four(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.BROCHURES,
        quantity=50,
        format="A5",
        material="120",
        sides=2,
        pages=10,
    )

    with pytest.raises(CalculationError, match="кратно 4"):
        calculate_quote(request, rates)


def test_banner_uses_linear_metres_and_finishing(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.BANNERS,
        quantity=2,
        width_mm=1200,
        height_mm=2000,
        material="banner_440",
        hemming=True,
        eyelets=8,
        markup_percent=0,
        include_vat=False,
    )

    quote = calculate_quote(request, rates)

    assert quote.production_units == Decimal("4.20")
    assert quote.base_cost == Decimal("3648.00")
    assert quote.total == Decimal("3648.00")


def test_minimum_order_is_applied(rates) -> None:
    request = QuoteRequest(
        product_type=ProductType.FLYERS,
        quantity=1,
        format="A6",
        material="90",
        sides=1,
        markup_percent=0,
        include_vat=False,
    )

    quote = calculate_quote(request, rates)

    assert quote.total == Decimal("100.00")
    assert quote.minimum_order_applied is True
