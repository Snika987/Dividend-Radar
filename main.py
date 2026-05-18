from fastmcp import FastMCP
import json
import os

from datetime import (
    datetime,
    timedelta
)

from dotenv import load_dotenv

from kiteconnect import KiteConnect

from market_data import (
    get_stock_dividends,
    get_market_symbols
)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Dividend Analyzer")

# Kite API Setup
KITE_API_KEY = os.getenv("KITE_API_KEY")
KITE_API_SECRET = os.getenv("KITE_API_SECRET")

# Kite session
kite = None


def init_kite_session():

    global kite

    try:

        kite = KiteConnect(
            api_key=KITE_API_KEY
        )

        kite_access_token = os.getenv(
            "KITE_ACCESS_TOKEN"
        )

        # Try existing token
        if (
            kite_access_token and
            kite_access_token !=
            "your_access_token_here"
        ):

            try:

                kite.set_access_token(
                    kite_access_token
                )

                kite.profile()

                print(
                    "✅ Existing Kite session restored"
                )

                return True

            except Exception:

                print(
                    "⚠ Existing token expired"
                )

        # No valid token
        login_url = kite.login_url()

        print("\n")
        print("🔐 Login required")
        print("Open this URL manually:")
        print(login_url)
        print("\n")
        print(
            "Run generate_token.py separately to refresh token."
        )
        print("\n")

        return False

    except Exception:

        import traceback
        traceback.print_exc()

        return False


def get_kite_portfolio() -> list | None:

    try:

        if not kite:
            return None

        holdings = kite.holdings()

        portfolio = []

        for holding in holdings:

            portfolio.append({

                "symbol":
                    holding.get(
                        "tradingsymbol"
                    ),

                "quantity":
                    holding.get(
                        "quantity"
                    ),

                "averagePrice":
                    holding.get(
                        "average_price"
                    ),

                "lastPrice":
                    holding.get(
                        "last_price"
                    ),

                "totalValue":
                    holding.get(
                        "quantity"
                    ) *
                    holding.get(
                        "last_price"
                    )
            })

        return portfolio

    except Exception:

        import traceback
        traceback.print_exc()

        return None


@mcp.tool
def get_my_portfolio() -> str:

    if not kite:

        return json.dumps({
            "error":
                "Kite session not initialized"
        })

    portfolio = get_kite_portfolio()

    if portfolio is None:

        return json.dumps({
            "error":
                "Failed to fetch portfolio"
        })

    return json.dumps({

        "totalHoldings":
            len(portfolio),

        "portfolio":
            portfolio,

        "timestamp":
            datetime.now().isoformat()
    })


@mcp.tool
def analyze_dividends_since_purchase(
    symbol: str = ""
) -> str:

    if not kite:

        return json.dumps({
            "error":
                "Kite session not initialized"
        })

    portfolio = get_kite_portfolio()

    if portfolio is None:

        return json.dumps({
            "error":
                "Failed to fetch portfolio"
        })

    if symbol.strip():

        portfolio = [

            p for p in portfolio

            if p["symbol"] ==
            symbol.upper()
        ]

    analysis = []

    for position in portfolio:

        stock_symbol = position["symbol"]

        dividends = get_stock_dividends(
            stock_symbol
        )

        dividends.sort(
            key=lambda x: x.get(
                "paymentDate",
                ""
            ),
            reverse=True
        )

        total_dividend_income = sum(

            d.get(
                "dividendAmount",
                0
            ) *
            position["quantity"]

            for d in dividends
        )

        analysis.append({

            "symbol":
                stock_symbol,

            "quantity":
                position["quantity"],

            "averagePrice":
                position["averagePrice"],

            "currentPrice":
                position["lastPrice"],

            "totalValue":
                position["totalValue"],

            "dividendsPaidTotal":
                len(dividends),

            "totalDividendIncome":
                round(
                    total_dividend_income,
                    2
                ),

            "dividendHistory": [

                {
                    "exDate":
                        d.get("exDate"),

                    "paymentDate":
                        d.get("paymentDate"),

                    "amountPerShare":
                        d.get(
                            "dividendAmount"
                        ),

                    "totalAmount":
                        round(
                            d.get(
                                "dividendAmount",
                                0
                            ) *
                            position["quantity"],
                            2
                        )
                }

                for d in dividends[:10]
            ]
        })

    total_dividend_across_portfolio = sum(
        a["totalDividendIncome"]
        for a in analysis
    )

    return json.dumps({

        "count":
            len(analysis),

        "analysis":
            analysis,

        "summary": {

            "totalDividendIncome":
                round(
                    total_dividend_across_portfolio,
                    2
                ),

            "stocksWithDividends":
                len([
                    a for a in analysis
                    if a[
                        "dividendsPaidTotal"
                    ] > 0
                ])
        },

        "timestamp":
            datetime.now().isoformat()
    })


@mcp.tool
def get_latest_dividend_announcements(
    limit: int = 10
) -> str:

    symbols = get_market_symbols()

    announcements = []

    cutoff_date = (
        datetime.now() -
        timedelta(days=90)
    )

    for symbol in symbols:

        dividends = get_stock_dividends(
            symbol
        )

        for d in dividends:

            try:

                dividend_date = (
                    datetime.fromisoformat(
                        d["exDate"]
                    )
                )

                if (
                    dividend_date >=
                    cutoff_date
                ):

                    announcements.append({

                        "symbol":
                            symbol,

                        "companyName":
                            symbol,

                        "exDate":
                            d.get(
                                "exDate"
                            ),

                        "recordDate":
                            d.get(
                                "recordDate"
                            ),

                        "paymentDate":
                            d.get(
                                "paymentDate"
                            ),

                        "dividendAmount":
                            d.get(
                                "dividendAmount"
                            )
                    })

            except Exception:
                continue

    announcements.sort(
        key=lambda x: x.get(
            "exDate",
            ""
        ),
        reverse=True
    )

    return json.dumps({

        "count":
            min(
                len(announcements),
                limit
            ),

        "announcements":
            announcements[:limit],

        "timestamp":
            datetime.now().isoformat()
    })


@mcp.resource(
    "info://dividend-analyzer"
)
def server_info() -> str:

    kite_status = (
        "Connected"
        if kite else
        "Not connected"
    )

    return json.dumps({

        "name":
            "Dividend Analyzer MCP",

        "status": {

            "kiteConnection":
                kite_status
        },

        "tools": [

            "get_my_portfolio",

            "analyze_dividends_since_purchase",

            "get_latest_dividend_announcements",

        ]

    }, indent=2)


if __name__ == "__main__":

    init_kite_session()

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8081
    )