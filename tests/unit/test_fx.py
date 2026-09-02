from decimal import Decimal

import pytest

from app.exceptions import ValidationAppError
from app.fx import get_fx_rate, to_usd


def test_usd_is_identity() -> None:
    rate, usd = to_usd(Decimal("100000"), "USD")
    assert rate == Decimal("1.00000000")
    assert usd == Decimal("100000.00")


def test_inr_snapshot_is_decimal() -> None:
    rate, usd = to_usd(Decimal("2000000"), "inr")
    assert rate == Decimal("0.01200000")
    assert usd == Decimal("24000.00")


def test_rejects_unknown_currency() -> None:
    with pytest.raises(ValidationAppError):
        get_fx_rate("XYZ")


def test_rejects_non_positive_salary() -> None:
    with pytest.raises(ValidationAppError):
        to_usd(Decimal("0"), "USD")
