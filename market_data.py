import yfinance as yf


def get_stock_dividends(symbol: str):

    try:

        ticker = yf.Ticker(f"{symbol}.NS")

        dividends = ticker.dividends

        results = []

        for date, amount in dividends.tail(20).items():

            results.append({
                "symbol": symbol,
                "exDate": str(date.date()),
                "recordDate": str(date.date()),
                "paymentDate": str(date.date()),
                "dividendAmount": float(amount),
                "dividendType": "Dividend"
            })

        return results

    except Exception as e:
        print(e)
        return []