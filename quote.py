import hashlib

BULK_QUANTITY = 10
BULK_PERCENT = 10
TAX_PERCENT = 5


def to_cents(price):
    return int(round(float(price) * 100))


def from_cents(cents):
    return cents / 100


def quote_code(lines):
    parts = [
        f"{line['id']}:{line['quantity']}"
        for line in sorted(lines, key=lambda line: line["id"])
    ]
    digest = hashlib.sha256(",".join(parts).encode()).hexdigest()
    return digest[:8]


def collect_lines(fetch_tool, orders):
    lines = []
    for tool_id, qty in orders:
        tool = fetch_tool(tool_id)
        lines.append(
            {
                "id": tool["id"],
                "name": tool["name"],
                "price": tool["price"],
                "stock": tool["quantity"],
                "quantity": qty,
            }
        )
    return lines


def build_quote(lines):
    if not lines:
        raise ValueError("quote needs at least one line")

    priced = []
    subtotal_cents = 0
    total_qty = 0
    for line in lines:
        qty = line["quantity"]
        stock = line["stock"]
        if qty < 1:
            raise ValueError(f"quantity must be at least 1 for {line['name']}")
        if qty > stock:
            raise ValueError(f"only {stock} of {line['name']} in stock")
        line_cents = to_cents(line["price"]) * qty
        subtotal_cents += line_cents
        total_qty += qty
        priced.append(
            {
                "id": line["id"],
                "name": line["name"],
                "quantity": qty,
                "line_total": from_cents(line_cents),
            }
        )

    if total_qty >= BULK_QUANTITY:
        discount_cents = subtotal_cents * BULK_PERCENT // 100
    else:
        discount_cents = 0
    taxable_cents = subtotal_cents - discount_cents
    tax_cents = taxable_cents * TAX_PERCENT // 100

    return {
        "lines": priced,
        "subtotal": from_cents(subtotal_cents),
        "discount": from_cents(discount_cents),
        "tax": from_cents(tax_cents),
        "total": from_cents(taxable_cents + tax_cents),
        "code": quote_code(lines),
    }
