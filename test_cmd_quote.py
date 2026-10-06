"""The same tests as test_cmd_quote.py, but with a fake client instead of the API.

cmd_quote only ever calls client.get_tool, so any object with that method will do.
Nothing here opens a socket, and no row is written to the database.
"""

from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO

import pytest

from api_client import ApiError
from main import cmd_quote

CATALOG = {
    1: {"id": 1, "name": "Hammer", "price": 10.0, "quantity": 12},
    5: {"id": 5, "name": "Pliers", "price": 4.0, "quantity": 8},
}


class FakeToolsClient:
    """Stands in for ToolsClient. Serves tools from a dictionary and records the ids asked for."""

    def __init__(self, catalog):
        self.catalog = catalog
        self.requested_ids = []

    def get_tool(self, tool_id):
        self.requested_ids.append(tool_id)
        try:
            return self.catalog[tool_id]
        except KeyError:
            raise ApiError(404, f"No tool found with id {tool_id}") from None


@pytest.fixture
def client():
    return FakeToolsClient(CATALOG)


def quote_output(client, *items):
    buffer = StringIO()
    with redirect_stdout(buffer):
        cmd_quote(client, Namespace(items=list(items)))
    return buffer.getvalue()


def test_two_units_have_no_discount(client):
    output = quote_output(client, "1:2")
    assert output == (
        "2 x Hammer  20.00\n"
        "subtotal 20.00\n"
        "discount 0.00\n"
        "tax      1.00\n"
        "total    21.00\n"
        "code     673aeeb0\n"
    )


def test_ten_units_get_bulk_discount(client):
    output = quote_output(client, "1:10")
    assert output == (
        "10 x Hammer  100.00\n"
        "subtotal 100.00\n"
        "discount 10.00\n"
        "tax      4.50\n"
        "total    94.50\n"
        "code     b37ae13e\n"
    )


def test_bulk_discount_spans_two_tools(client):
    output = quote_output(client, "1:6", "5:4")
    assert output == (
        "6 x Hammer  60.00\n"
        "4 x Pliers  16.00\n"
        "subtotal 76.00\n"
        "discount 7.60\n"
        "tax      3.42\n"
        "total    71.82\n"
        "code     e860b047\n"
    )


def test_quantity_above_stock_is_rejected(client):
    with pytest.raises(ValueError, match="only 12"):
        quote_output(client, "1:13")


def test_missing_tool_raises_api_error(client):
    with pytest.raises(ApiError) as caught:
        quote_output(client, "999:1")
    assert caught.value.status_code == 404


def test_malformed_order_is_rejected_before_any_lookup(client):
    with pytest.raises(ValueError, match="expected id:quantity"):
        quote_output(client, "hammer")
    assert client.requested_ids == []


def test_each_ordered_tool_is_fetched_once(client):
    quote_output(client, "1:2", "5:1")
    assert client.requested_ids == [1, 5]
