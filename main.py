from fastmcp import FastMCP
import json
import os
import webbrowser
from datetime import datetime
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from market_data import get_stock_dividends

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Dividend Analyzer")

# Kite API Setup
KITE_API_KEY = os.getenv("KITE_API_KEY")
KITE_API_SECRET = os.getenv("KITE_API_SECRET")

# Kite session
kite = None


def save_access_token_to_env(access_token: str):
    """Save access token to .env file"""

    try:

        env_path = ".env"

        with open(env_path, "r") as f:
            lines = f.readlines()

        updated = False
        new_lines = []

        for line in lines:

            if line.startswith("KITE_ACCESS_TOKEN="):
                new_lines.append(
                    f"KITE_ACCESS_TOKEN={access_token}\n"
                )
                updated = True

            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(
                f"KITE_ACCESS_TOKEN={access_token}\n"
            )

        with open(env_path, "w") as f:
            f.writelines(new_lines)

    except Exception:
        pass


def init_kite_session():
    """Initialize Kite session"""

    global kite

    try:

        kite = KiteConnect(api_key=KITE_API_KEY)

        kite_access_token = os.getenv(
            "KITE_ACCESS_TOKEN"
        )

        # Try saved token first
        if (
            kite_access_token and
            kite_access_token != "your_access_token_here"
        ):

            try:

                kite.set_access_token(
                    kite_access_token
                )

                kite.profile()

                print("Using saved Kite token")

                return True

            except Exception:
                pass

        # Interactive login
        login_url = kite.login_url()

        try:
            webbrowser.open(login_url)
        except Exception:
            pass

        request_token = input(
            "Enter request_token from redirect URL: "
        ).strip()

        if not request_token:
            return False

        session_data = kite.generate_session(
            request_token,
            KITE_API_SECRET
        )

        access_token = session_data[
            "access_token"
        ]

        kite.set_access_token(access_token)

        kite.profile()

        save_access_token_to_env(access_token)

        return True

    except Exception as e:

        import traceback
        traceback.print_exc()

        return False


def get_kite_portfolio():
    """Fetch portfolio from Kite"""

    try:

        if not kite:
            return None

        holdings = kite.holdings()

        portfolio = []

        for holding in holdings:

            portfolio.append({
                "symbol": holding.get(
                    "tradingsymbol"
                ),
                "quantity": holding.get(
                    "quantity"
                ),
                "averagePrice": holding.get(
                    "average_price"
                ),
                "lastPrice": holding.get(
                    "last_price"
                ),
                "totalValue": (
                    holding.get("quantity") *
                    holding.get("last_price")
                )
            })

        return portfolio

    except Exception:
        return None


# ================= TOOLS =================


@mcp.tool
def get_my_portfolio() -> str:
    """Retrieve live stock portfolio"""

    if not kite:

        return json.dumps({
            "error": "Kite session not initialized"
        })

    portfolio = get_kite_portfolio()

    if portfolio is None:

        return json.dumps({
            "error": "Failed to fetch portfolio"
        })

    return json.dumps({
        "totalHoldings": len(portfolio),
        "portfolio": portfolio,
        "timestamp": datetime.now().isoformat()
    })


@mcp.tool
def analyze_dividends_since_purchase(
    symbol: str = ""
) -> str:
    """Analyze dividend payments"""

    if not kite:

        return json.dumps({
            "error": "Kite session not initialized"
        })

    portfolio = get_kite_portfolio()

    if portfolio is None:

        return json.dumps({
            "error": "Failed to fetch portfolio"
        })

    if symbol.strip():

        portfolio = [
            p for p in portfolio
            if p["symbol"] == symbol.upper()
        ]

    if not portfolio:

        return json.dumps({
            "error": f"{symbol} not found"
        })

    analysis = []

    for position in portfolio:

        stock_symbol = position["symbol"]

        dividends = get_stock_dividends(
            stock_symbol
        )

        relevant_dividends = sorted(
            dividends,
            key=lambda x: x.get(
                "paymentDate", ""
            ),
            reverse=True
        )

        total_dividend_income = sum(
            d.get("dividendAmount", 0) *
            position["quantity"]
            for d in relevant_dividends
        )

        analysis.append({

            "symbol": stock_symbol,

            "quantity": position["quantity"],

            "averagePrice":
                position["averagePrice"],

            "currentPrice":
                position["lastPrice"],

            "totalValue":
                position["totalValue"],

            "dividendsPaidTotal":
                len(relevant_dividends),

            "totalDividendIncome":
                round(total_dividend_income, 2),

            "dividendHistory": [

                {
                    "exDate":
                        d.get("exDate"),

                    "paymentDate":
                        d.get("paymentDate"),

                    "amountPerShare":
                        d.get("dividendAmount"),

                    "totalAmount":
                        round(
                            d.get(
                                "dividendAmount",
                                0
                            ) * position["quantity"],
                            2
                        )
                }

                for d in relevant_dividends[:10]
            ]
        })

    total_dividend_across_portfolio = sum(
        a["totalDividendIncome"]
        for a in analysis
    )

    return json.dumps({

        "count": len(analysis),

        "analysis": analysis,

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
    limit: int = 50
) -> str:
    """Get latest dividend announcements"""

    symbols = [
        "RELIANCE",
        "NTPC",
        "POWERGRID",
        "IRFC",
        "IRCON"
    ]

    announcements = []

    for symbol in symbols:

        dividends = get_stock_dividends(
            symbol
        )

        for d in dividends[:3]:

            announcements.append({

                "symbol": symbol,

                "companyName": symbol,

                "exDate":
                    d.get("exDate"),

                "recordDate":
                    d.get("recordDate"),

                "paymentDate":
                    d.get("paymentDate"),

                "dividendAmount":
                    d.get("dividendAmount")
            })

    announcements.sort(
        key=lambda x: x.get(
            "exDate", ""
        ),
        reverse=True
    )

    return json.dumps({

        "count":
            min(len(announcements), limit),

        "announcements":
            announcements[:limit],

        "timestamp":
            datetime.now().isoformat()
    })


@mcp.tool
def find_high_dividend_stocks(
    min_dividend: float = 2.0
) -> str:
    """Find high dividend stocks"""

    symbols = [
        "RELIANCE",
        "NTPC",
        "POWERGRID",
        "IRFC",
        "IRCON"
    ]

    announcements = []

    for symbol in symbols:

        dividends = get_stock_dividends(
            symbol
        )

        for d in dividends[:3]:

            announcements.append({

                "symbol": symbol,

                "companyName": symbol,

                "exDate":
                    d.get("exDate"),

                "recordDate":
                    d.get("recordDate"),

                "paymentDate":
                    d.get("paymentDate"),

                "dividendAmount":
                    d.get("dividendAmount")
            })

    high_div_stocks = [

        a for a in announcements

        if a.get(
            "dividendAmount",
            0
        ) >= min_dividend
    ]

    high_div_stocks.sort(
        key=lambda x: x.get(
            "dividendAmount",
            0
        ),
        reverse=True
    )

    return json.dumps({

        "count": len(high_div_stocks),

        "criteria":
            f"Minimum dividend: ₹{min_dividend}",

        "stocks":
            high_div_stocks[:50],

        "timestamp":
            datetime.now().isoformat()
    })


# ================= RESOURCE =================


@mcp.resource("info://dividend-analyzer")
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

            "find_high_dividend_stocks"
        ]

    }, indent=2)


# ================= MAIN =================


if __name__ == "__main__":

    init_kite_session()

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080
    )