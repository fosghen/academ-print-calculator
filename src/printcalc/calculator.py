"""Pure, deterministic quote calculations."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from printcalc.models import ProductType, Quote, QuoteLine, QuoteRequest

if TYPE_CHECKING:
    from printcalc.rates import Rates, RateTier

MONEY = Decimal("0.01")


class CalculationError(ValueError):
    """Raised when a requested product cannot be produced by configured rules."""


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _ceil(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def _tier_price(tiers: list[RateTier], quantity: int) -> Decimal:
    for tier in tiers:
        if tier.max_quantity is None or quantity <= tier.max_quantity:
            return tier.price
    msg = "Для этого тиража не настроен тариф."
    raise CalculationError(msg)


def _business_cards(
    request: QuoteRequest, rates: Rates
) -> tuple[Decimal, Decimal, list[QuoteLine]]:
    try:
        prices = rates.business_cards.prices[request.material][str(request.sides)]
        price = prices[request.quantity]
    except KeyError as error:
        msg = "Такой материал, цветность или тираж визиток пока не настроен."
        raise CalculationError(msg) from error
    amount = _money(price)
    return Decimal(request.quantity), amount, [QuoteLine(label="Печать визиток", amount=amount)]


def _digital_sheets(request: QuoteRequest, rates: Rates, *, brochure: bool) -> tuple[int, int]:
    try:
        up = rates.digital_print.formats_up[request.format]
    except KeyError as error:
        msg = "Выбранный формат не поддерживается."
        raise CalculationError(msg) from error
    if brochure:
        if request.pages % 4 != 0:
            msg = "Количество страниц брошюры должно быть кратно 4."
            raise CalculationError(msg)
        sheets = _ceil(Decimal(request.quantity * request.pages) / Decimal(2 * up))
    else:
        sheets = _ceil(Decimal(request.quantity) / Decimal(up))
    return sheets, up


def _digital(
    request: QuoteRequest, rates: Rates, *, brochure: bool
) -> tuple[Decimal, Decimal, list[QuoteLine]]:
    sheets, _ = _digital_sheets(request, rates, brochure=brochure)
    try:
        tiers = rates.digital_print.prices[str(request.sides)][request.material]
    except KeyError as error:
        msg = "Для выбранной бумаги и цветности нет тарифа."
        raise CalculationError(msg) from error

    print_cost = _money(Decimal(sheets) * _tier_price(tiers, sheets))
    lines = [QuoteLine(label=f"Цифровая печать: {sheets} лист.", amount=print_cost)]
    total = print_cost
    if request.cutting:
        total += rates.digital_print.cutting
        lines.append(QuoteLine(label="Резка тиража", amount=rates.digital_print.cutting))
    if brochure:
        binding = _money(Decimal(request.quantity) * rates.digital_print.saddle_stitch)
        total += binding
        lines.append(QuoteLine(label="Скрепление на скобу", amount=binding))
    return Decimal(sheets), _money(total), lines


def _banner(request: QuoteRequest, rates: Rates) -> tuple[Decimal, Decimal, list[QuoteLine]]:
    try:
        material = rates.banners.materials[request.material]
    except KeyError as error:
        msg = "Материал для широкоформатной печати не настроен."
        raise CalculationError(msg) from error
    if request.width_mm > material.max_width_mm:
        msg = f"Ширина превышает доступные {material.max_width_mm} мм."
        raise CalculationError(msg)

    height_metres = Decimal(request.height_mm) / Decimal(1000)
    waste = Decimal(1) + rates.banners.waste_percent / Decimal(100)
    linear_metres = (height_metres * request.quantity * waste).quantize(Decimal("0.01"))
    print_cost = _money(linear_metres * material.price_per_linear_metre)
    lines = [QuoteLine(label=f"Печать: {linear_metres} пог. м", amount=print_cost)]
    total = print_cost

    if request.hemming:
        perimeter = (
            Decimal(2)
            * (Decimal(request.width_mm + request.height_mm) / Decimal(1000))
            * request.quantity
        )
        hemming = _money(perimeter * rates.banners.hemming_per_metre)
        total += hemming
        lines.append(QuoteLine(label="Подгибка края", amount=hemming))
    if request.eyelets:
        eyelets = _money(Decimal(request.eyelets * request.quantity) * rates.banners.eyelet)
        total += eyelets
        lines.append(QuoteLine(label="Установка люверсов", amount=eyelets))
    return linear_metres, _money(total), lines


def calculate_quote(request: QuoteRequest, rates: Rates) -> Quote:
    """Calculate a quote from normalized input and a versioned rate card."""
    if request.product_type is ProductType.BUSINESS_CARDS:
        units, base, lines = _business_cards(request, rates)
    elif request.product_type is ProductType.FLYERS:
        units, base, lines = _digital(request, rates, brochure=False)
    elif request.product_type is ProductType.BROCHURES:
        units, base, lines = _digital(request, rates, brochure=True)
    else:
        units, base, lines = _banner(request, rates)

    markup = _money(base * request.markup_percent / Decimal(100))
    vat_base = base + markup
    vat = _money(vat_base * rates.vat_percent / Decimal(100)) if request.include_vat else Decimal(0)
    calculated = _money(vat_base + vat)
    minimum_applied = calculated < rates.minimum_order
    total = rates.minimum_order if minimum_applied else calculated
    return Quote(
        product_type=request.product_type,
        quantity=request.quantity,
        production_units=units,
        lines=lines,
        base_cost=base,
        markup=markup,
        vat=vat,
        total=_money(total),
        unit_price=_money(total / Decimal(request.quantity)),
        minimum_order_applied=minimum_applied,
    )
