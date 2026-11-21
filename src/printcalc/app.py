"""FastAPI web interface for the printing calculator."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from printcalc.calculator import CalculationError, calculate_quote
from printcalc.models import ProductType, QuoteRequest
from printcalc.rates import Rates, load_rates

if TYPE_CHECKING:
    from starlette.datastructures import FormData

PACKAGE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
app = FastAPI(title="Калькулятор Академ-принт", version="0.1.0")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
RATES: Rates = load_rates()


def _ruble(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


templates.env.filters["ruble"] = _ruble


def _text(form: FormData, key: str, default: str) -> str:
    value = form.get(key, default)
    return value if isinstance(value, str) else default


def _integer(form: FormData, key: str, default: int) -> int:
    try:
        return int(_text(form, key, str(default)))
    except ValueError:
        return default


def _decimal(form: FormData, key: str, default: Decimal) -> Decimal:
    try:
        return Decimal(_text(form, key, str(default)).replace(",", "."))
    except InvalidOperation:
        return default


def _request_from_form(form: FormData) -> QuoteRequest:
    return QuoteRequest(
        product_type=ProductType(_text(form, "product_type", ProductType.BUSINESS_CARDS)),
        quantity=_integer(form, "quantity", 96),
        format=_text(form, "format", "A5"),
        material=_text(form, "material", "smooth"),
        sides=_integer(form, "sides", 1),
        pages=_integer(form, "pages", 4),
        width_mm=_integer(form, "width_mm", 1000),
        height_mm=_integer(form, "height_mm", 1000),
        cutting="cutting" in form,
        hemming="hemming" in form,
        eyelets=_integer(form, "eyelets", 0),
        markup_percent=_decimal(form, "markup_percent", Decimal(20)),
        include_vat="include_vat" in form,
    )


def _context(request: Request, *, form: dict[str, str] | None = None) -> dict[str, object]:
    return {
        "request": request,
        "quote": None,
        "error": None,
        "form": form or {},
        "rate_version": RATES.version,
    }


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    """Return a dependency-free liveness signal."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def calculator_page(request: Request) -> HTMLResponse:
    """Render the calculator with sensible defaults."""
    return templates.TemplateResponse(request, "calculator.html", _context(request))


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(request: Request) -> HTMLResponse:
    """Validate submitted parameters and render an explainable quote."""
    form = await request.form()
    context = _context(
        request,
        form={key: value for key, value in form.items() if isinstance(value, str)},
    )
    try:
        quote_request = _request_from_form(form)
        context["quote"] = calculate_quote(quote_request, RATES)
    except (CalculationError, ValidationError, ValueError) as error:
        context["error"] = str(error)
        return templates.TemplateResponse(request, "calculator.html", context, status_code=422)
    return templates.TemplateResponse(request, "calculator.html", context)
