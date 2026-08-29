from decimal import ROUND_HALF_UP, Decimal

from app.core.exceptions import ValidationAppError

# Static reference rates: 1 unit of currency -> USD.
# Historical compensation stores the rate used at write time.
FX_TO_USD: dict[str, Decimal] = {
    "USD": Decimal("1.00000000"),
    "GBP": Decimal("1.27000000"),
    "EUR": Decimal("1.08000000"),
    "INR": Decimal("0.01200000"),
    "CAD": Decimal("0.73000000"),
    "SGD": Decimal("0.74000000"),
    "AUD": Decimal("0.65000000"),
    "BRL": Decimal("0.18000000"),
    "JPY": Decimal("0.00670000"),
}

MONEY = Decimal("0.01")


def supported_currencies() -> list[str]:
    return sorted(FX_TO_USD)


def get_fx_rate(currency: str) -> Decimal:
    code = currency.upper()
    if code not in FX_TO_USD:
        raise ValidationAppError(f"Unsupported currency: {currency}")
    return FX_TO_USD[code]


def to_usd(annual_salary: Decimal, currency: str) -> tuple[Decimal, Decimal]:
    """Return (fx_rate_to_usd, annual_salary_usd) using the current reference table."""
    if annual_salary <= 0:
        raise ValidationAppError("annual_salary must be greater than zero")
    rate = get_fx_rate(currency)
    usd = (annual_salary * rate).quantize(MONEY, rounding=ROUND_HALF_UP)
    return rate, usd
