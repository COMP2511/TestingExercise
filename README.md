# Tool quote desk

A small command-line program that reads the tools catalog and builds a quote the API does not provide. Stock checks, discount, tax, and the quote code live in plain functions, so they can be unit-tested without calling the server.


## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

The server address is not in the source. Put it in `.env`, which is gitignored:

```
TOOLS_API_BASE=http://your-server:5000
```

Three places can supply it, most specific first: the `--base-url` option, the `TOOLS_API_BASE` environment variable, then `.env`. With none of them set, the client falls back to `http://127.0.0.1:5000`.

## Commands

List tools, optionally filtered by name:

```bash
python main.py list
python main.py list --name pliers
```

Show one tool's price and stock:

```bash
python main.py show 1
```

Quote one or more `id:quantity` pairs. The program loads each tool, then prints the subtotal, discount, tax, total, and an 8-character quote code:

```bash
python main.py quote 1:2
python main.py quote 1:2 5:1
```

Add a tool. A new UUID is sent as the `Idempotency-Key` header:

```bash
python main.py add "Safety Glasses" 10 4.50
```

## Quote rules

Money is calculated in cents.

- A quantity under 1, or above the tool's stock, is rejected.
- Line total is price times quantity. Subtotal is the sum of the line totals.
- An order of 10 or more units gets 10% off the subtotal.
- Tax is 5% of the discounted subtotal.
- Total is subtotal minus discount plus tax.
- The quote code is the first 8 hex characters of a SHA-256 hash of `id:quantity` pairs, sorted by id. The same cart always produces the same code.

## Files

| File | Responsibility |
| --- | --- |
| `api_client.py` | HTTP only. Calls health, list, get, and create, and raises `ApiError` on an error response. |
| `quote.py` | Pricing rules. `collect_lines` accepts any fetch function. `build_quote` and `quote_code` work on plain dictionaries. |
| `main.py` | Command-line program. Fetches tools, then calls the functions in `quote.py`. |
| `test_quote.py` | Equivalence-class tests for `build_quote`. They use plain dictionaries and do not call the API. |
| `test_cmd_quote.py` | Tests for `cmd_quote`. They use the real `ToolsClient` and the live API. |
| `test_cmd_quote_isolated.py` | The same tests for `cmd_quote`, run against a hand-written fake client with no network. |
| `test_cmd_quote_mocked.py` | The same tests again, with `requests.request` replaced by a `Mock` that is verified for how it was called. |
| `requirements.txt` | `requests` for the API client, and `pytest` for the tests. |

## Tests
This section is your task to complete.