import pytest

from quote import build_quote


def hammer(quantity, stock=12):
    return {
        "id": 1,
        "name": "Hammer",
        "price": 10.0,
        "stock": stock,
        "quantity": quantity,
    }


def test_empty_quote_is_rejected():
    with pytest.raises(ValueError, match="at least one line"):
        build_quote([])


def test_quantity_below_one_is_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        build_quote([hammer(0)])


def test_small_order_has_no_discount():
    quote = build_quote([hammer(2)])
    assert quote["subtotal"] == 20.0
    assert quote["discount"] == 0.0
    assert quote["tax"] == 1.0
    assert quote["total"] == 21.0
    assert quote["code"] == "673aeeb0"


def test_bulk_order_takes_ten_percent():
    quote = build_quote([hammer(10)])
    assert quote["subtotal"] == 100.0
    assert quote["discount"] == 10.0
    assert quote["tax"] == 4.5
    assert quote["total"] == 94.5
    assert quote["code"] == "b37ae13e"


def test_quantity_above_stock_is_rejected():
    with pytest.raises(ValueError, match="only 12"):
        build_quote([hammer(13)])


def pliers(quantity, stock=8):
    return {
        "id": 5,
        "name": "Pliers",
        "price": 4.0,
        "stock": stock,
        "quantity": quantity,
    }


def test_bulk_discount_applies_across_different_tools():
    hammers = hammer(6)
    pairs = pliers(4)
    quote = build_quote([hammers, pairs])
    assert quote["lines"] == [
        {"id": 1, "name": "Hammer", "quantity": 6, "line_total": 60.0},
        {"id": 5, "name": "Pliers", "quantity": 4, "line_total": 16.0},
    ]
    assert quote["subtotal"] == 76.0
    assert quote["discount"] == 7.6
    assert quote["tax"] == 3.42
    assert quote["total"] == 71.82
    assert quote["code"] == "e860b047"
    assert build_quote([pairs, hammers])["code"] == quote["code"]
