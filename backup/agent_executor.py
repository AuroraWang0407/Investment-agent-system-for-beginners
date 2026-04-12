import yfinance as yf
import requests


# Original stock price query function (unchanged)
@tool
def get_stock_data(ticker):

    """
    Get the current price and basic information of a specified stock.
    """
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        return {
            "ticker": ticker,
            "current_price": price
        }
    except Exception as e:
        return {"ticker": ticker, "current_price": 0}


# ==============================================
# Brand New Financial News Function (Alpha Vantage)
# ==============================================

@tool
def get_stock_news(ticker):

    """
    Get the latest related news about a specific stock
    """

    API_KEY = "L0LH6HPYUZ1O7WVD"
    url = f"https://www.alphavantage.co/query"

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": API_KEY,
        "limit": 10  # Fetch 10 items first for better filtering accuracy
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        news_list = []
        # Filter: Title/URL contains ticker (case-insensitive)
        for item in data.get("feed", []):
            if ticker.lower() in item.get("title", "").lower() or ticker.lower() in item.get("url", "").lower():
                news_list.append({
                    "title": item.get("title", "No Title"),
                    "publisher": item.get("source", "Unknown Publisher"),
                    "link": item.get("url", ""),
                    "publish_time": item.get("time_published", "")
                })
            # Keep only top 5 matching news items
            if len(news_list) >= 5:
                break

        # Return prompt if no filtered data
        if not news_list:
            news_list.append({
                "title": f"No relevant news found for {ticker}.",
                "publisher": "System",
                "link": "",
                "publish_time": ""
            })

        return {
            "ticker": ticker,
            "news_list": news_list
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "news_list": [{
                "title": f"Could not retrieve news for {ticker} at this moment.",
                "publisher": "System",
                "link": "",
                "publish_time": ""
            }]
        }

# Tool list (unchanged)
INVEST_TOOLS = {
    "get_stock_data": get_stock_data,
    "get_stock_news": get_stock_news
}


# Execute tool commands (unchanged)
def execute_tool_commands(commands):
    results = {}
    for cmd in commands:
        tool_name = cmd["tool"]
        params = cmd["params"]
        if tool_name in INVEST_TOOLS:
            res = INVEST_TOOLS[tool_name](**params)
            results[tool_name] = res
    return results