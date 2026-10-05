import argparse
import sys
import uuid

from api_client import ApiError, ToolsClient
from quote import build_quote, collect_lines


def parse_order(text):
    try:
        tool_id, qty = text.split(":", 1)
        return int(tool_id), int(qty)
    except ValueError:
        raise ValueError(f"expected id:quantity, got {text}") from None


def cmd_list(client, args):
    for tool in client.list_tools(args.name):
        print(f"{tool['id']:>4}  {tool['name']}")


def cmd_show(client, args):
    tool = client.get_tool(args.tool_id)
    print(f"{tool['name']} (id {tool['id']})")
    print(f"price {tool['price']:.2f}  stock {tool['quantity']}")


def cmd_quote(client, args):
    orders = [parse_order(item) for item in args.items]
    quote = build_quote(collect_lines(client.get_tool, orders))
    for line in quote["lines"]:
        print(f"{line['quantity']} x {line['name']}  {line['line_total']:.2f}")
    print(f"subtotal {quote['subtotal']:.2f}")
    print(f"discount {quote['discount']:.2f}")
    print(f"tax      {quote['tax']:.2f}")
    print(f"total    {quote['total']:.2f}")
    print(f"code     {quote['code']}")


def cmd_add(client, args):
    created = client.create_tool(
        args.name, args.quantity, args.price, str(uuid.uuid4())
    )
    print(f"created {created['id']}  {created['name']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tool quote desk")
    parser.add_argument("--base-url", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--name")
    list_cmd.set_defaults(func=cmd_list)

    show_cmd = sub.add_parser("show")
    show_cmd.add_argument("tool_id", type=int)
    show_cmd.set_defaults(func=cmd_show)

    quote_cmd = sub.add_parser("quote")
    quote_cmd.add_argument("items", nargs="+", help="id:quantity, for example 1:2")
    quote_cmd.set_defaults(func=cmd_quote)

    add_cmd = sub.add_parser("add")
    add_cmd.add_argument("name")
    add_cmd.add_argument("quantity", type=int)
    add_cmd.add_argument("price", type=float)
    add_cmd.set_defaults(func=cmd_add)

    args = parser.parse_args(argv)
    try:
        args.func(ToolsClient(args.base_url), args)
    except (ApiError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
