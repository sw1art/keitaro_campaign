"""Country reference data (ISO 3166-1 alpha-2)."""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _country_pairs() -> list[tuple[str, str]]:
    try:
        import pycountry

        pairs: list[tuple[str, str]] = []
        for c in pycountry.countries:
            code = getattr(c, "alpha_2", None)
            name = getattr(c, "name", None) or getattr(c, "common_name", None)
            if code and name:
                pairs.append((code.upper(), name))
        return sorted(pairs, key=lambda p: p[1].lower())
    except Exception:  # pragma: no cover - fallback list if pycountry is unavailable
        logger.exception("pycountry unavailable, using fallback country list")
        return [
            ("AU", "Australia"),
            ("MX", "Mexico"),
            ("RO", "Romania"),
            ("DE", "Germany"),
            ("PL", "Poland"),
            ("US", "United States"),
            ("GB", "United Kingdom"),
            ("FR", "France"),
            ("ES", "Spain"),
            ("IT", "Italy"),
            ("BR", "Brazil"),
            ("CA", "Canada"),
            ("IN", "India"),
            ("CN", "China"),
            ("JP", "Japan"),
        ]


def get_countries() -> list[dict[str, str]]:
    return [{"code": code, "name": name} for code, name in _country_pairs()]


def get_valid_geo_codes() -> set[str]:
    return {code for code, _ in _country_pairs()}
