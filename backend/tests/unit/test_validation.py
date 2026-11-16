"""Unit tests: GEO and offer share validation."""
import pytest

from app.domain.exceptions import BusinessRuleError, ValidationError
from app.domain.value_objects import (
    normalize_geo_code,
    validate_geo_codes,
    validate_offer_shares,
)


def test_normalize_geo_lowercase():
    assert normalize_geo_code("au") == "AU"


def test_normalize_geo_trims():
    assert normalize_geo_code("  mx ") == "MX"


@pytest.mark.parametrize("bad", ["A", "AUS", "A1", "", None, 123])
def test_normalize_geo_invalid(bad):
    with pytest.raises(ValidationError):
        normalize_geo_code(bad)


def test_validate_geo_empty():
    with pytest.raises(ValidationError):
        validate_geo_codes([])


def test_validate_geo_duplicate():
    with pytest.raises(ValidationError):
        validate_geo_codes(["AU", "au"])


def test_validate_geo_unknown_code():
    with pytest.raises(ValidationError):
        validate_geo_codes(["XX"], valid_codes={"AU", "MX"})


def test_validate_geo_ok():
    assert validate_geo_codes(["au", "MX"]) == ["AU", "MX"]


def test_validate_offer_shares_empty():
    with pytest.raises(BusinessRuleError):
        validate_offer_shares([])


def test_validate_offer_shares_empty_allowed_when_configured():
    assert validate_offer_shares([], require_at_least_one=False) == []


def test_validate_offer_shares_negative():
    with pytest.raises(ValidationError):
        validate_offer_shares([{"offer_id": 1, "share": -5}])


def test_validate_offer_shares_zero():
    with pytest.raises(ValidationError):
        validate_offer_shares([{"offer_id": 1, "share": 0}])


def test_validate_offer_shares_duplicate_offer():
    with pytest.raises(ValidationError):
        validate_offer_shares(
            [{"offer_id": 1, "share": 10}, {"offer_id": 1, "share": 20}]
        )


def test_validate_offer_shares_over_100():
    with pytest.raises(ValidationError):
        validate_offer_shares([{"offer_id": 1, "share": 200}])


def test_validate_offer_shares_rejects_fraction():
    with pytest.raises(ValidationError):
        validate_offer_shares([{"offer_id": 1, "share": 50.5}])


def test_validate_offer_shares_ok():
    result = validate_offer_shares([{"offer_id": 1, "share": 10}, {"offer_id": 2, "share": 100}])
    assert result == [{"offer_id": 1, "share": 10}, {"offer_id": 2, "share": 100}]
