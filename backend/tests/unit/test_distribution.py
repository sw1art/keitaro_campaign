"""Unit tests: traffic distribution calculation."""

from app.domain.value_objects import calculate_distribution


def test_distribution_basic_example():
    offers = [
        {"offer_id": 1, "share": 200},
        {"offer_id": 2, "share": 100},
        {"offer_id": 3, "share": 100},
    ]
    assert calculate_distribution(offers) == {1: 50.0, 2: 25.0, 3: 25.0}


def test_distribution_empty():
    assert calculate_distribution([]) == {}


def test_distribution_zero_total():
    assert calculate_distribution([{"offer_id": 1, "share": 0}]) == {}


def test_distribution_single_offer():
    assert calculate_distribution([{"offer_id": 1, "share": 100}]) == {1: 100.0}


def test_distribution_rounds_to_two_decimals():
    offers = [
        {"offer_id": 1, "share": 1},
        {"offer_id": 2, "share": 1},
        {"offer_id": 3, "share": 1},
    ]
    assert calculate_distribution(offers) == {1: 33.33, 2: 33.33, 3: 33.33}


def test_distribution_accepts_floats():
    offers = [
        {"offer_id": 1, "share": 1.5},
        {"offer_id": 2, "share": 0.5},
    ]
    assert calculate_distribution(offers) == {1: 75.0, 2: 25.0}
