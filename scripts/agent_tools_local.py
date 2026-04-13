"""

工具清单，可供 llm 自行选择

"""


import yfinance as yf
import requests
from langchain_classic.agents import tool
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool


# 显式内存：存储当前会话的参数
_memory_store = {
    "ticker": "None",
    "amount": 0.0,
    "loss_pct": 8.0  # 默认值
}


@tool
def get_current_quote(ticker: str) -> dict:
    """
    Fetch the latest real-time quote for a stock ticker.
    Returns current price, change, volume, day's range, etc.
    Useful for beginners who want to know the current price quickly.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        quote = {
            "ticker": ticker.upper(),
            "company_name": info.get("shortName", "Unknown"),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
            "previous_close": info.get("regularMarketPreviousClose", None),
            "change": info.get("regularMarketChange", None),
            "change_percent": info.get("regularMarketChangePercent", None),
            "day_high": info.get("regularMarketDayHigh", None),
            "day_low": info.get("regularMarketDayLow", None),
            "volume": info.get("regularMarketVolume", None),
            "currency": info.get("currency", "USD"),
            "market_state": info.get("marketState", "Unknown"),
        }

        # Format percentage nicely
        if quote["change_percent"] is not None:
            quote["change_percent"] = round(quote["change_percent"] * 100, 2)

        return quote

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "error": f"Failed to fetch quote: {str(e)}"
        }

@tool
def get_company_profile(ticker: str) -> dict:
    """
    Get basic company information: name, sector, industry, business summary,
    market cap, website, etc. Helpful for beginners who want to understand
    what the company actually does.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        profile = {
            "ticker": ticker.upper(),
            "company_name": info.get("shortName", "Unknown"),
            "full_name": info.get("longName", None),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", None),
            "business_summary": info.get("longBusinessSummary", "No description available"),
            "website": info.get("website", None),
            "country": info.get("country", None),
            "city": info.get("city", None),
            "employees": info.get("fullTimeEmployees", None),
            "trailing_pe": info.get("trailingPE", None),
            "forward_pe": info.get("forwardPE", None),
            "dividend_yield": info.get("dividendYield", None),
        }

        # Shorten long descriptions for readability
        if profile["business_summary"] and len(profile["business_summary"]) > 350:
            profile["business_summary"] = profile["business_summary"][:350] + "... (truncated)"

        return profile

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "error": str(e)
        }


# ==============================================
# Brand New Financial News Function (Alpha Vantage)
# ==============================================


@tool
def get_recent_news(ticker: str, limit: int = 5) -> dict:
    """
    Retrieves the latest stock news using the official LangChain YahooFinanceNewsTool.
    This is more reliable than Alpha Vantage, providing news directly relevant to the company itself.
    """
    try:
        tool = YahooFinanceNewsTool()
        raw_news = tool.run(ticker.upper())
        
        # You can perform simple parsing here to convert raw_news into a structured list 
        # (adjust based on actual output).
        # raw_news is typically a long string; you can split it by line or extract using simple rules.
        return {
            "ticker": ticker.upper(),
            "news_source": "Yahoo Finance",
            "raw_news": raw_news[:5000],   # Limit length to stay within LLM context windows
            "note": "Above are the summaries of recent relevant news. Please summarize the market sentiment."
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)}


# print(get_recent_news("TSLA"))


@tool
def calculate_position_size(
    budget_usd: float,
    current_price: float,
    max_loss_percent: float = 8.0,
    round_to_whole_shares: bool = True) -> dict:
    """
    Calculate how many shares a beginner can buy with their budget,
    the stop-loss price, and the maximum possible loss amount.
    
    Very useful for people new to investing who want to know position size
    and risk in dollars before buying.
    """
    if current_price <= 0:
        return {"error": "Current price must be positive"}

    # Number of shares
    shares = budget_usd / current_price

    if round_to_whole_shares:
        shares = round(shares)              # whole shares only
    else:
        shares = round(shares, 2)           # allow fractional shares

    actual_cost = shares * current_price
    stop_price = current_price * (1 - max_loss_percent / 100)
    max_loss_usd = (current_price - stop_price) * shares

    return {
        "budget_usd": budget_usd,
        "current_price_usd": current_price,
        "suggested_shares": shares,
        "estimated_cost_usd": round(actual_cost, 2),
        "stop_loss_price": round(stop_price, 2),
        "max_possible_loss_usd": round(max_loss_usd, 2),
        "max_loss_percent_used": max_loss_percent,
    }


@tool
def analyze_risk_reward(current_price: float, stop_loss_price: float, target_profit_pct: float = 20.0) -> dict:
    """
    Calculates the risk-reward ratio for a potential trade. 
    Helps beginners understand if the potential gain justifies the potential loss.
    """
    risk_per_share = current_price - stop_loss_price
    potential_gain_per_share = current_price * (target_profit_pct / 100)
    
    rr_ratio = potential_gain_per_share / risk_per_share if risk_per_share > 0 else 0
    
    return {
        "risk_per_share": round(risk_per_share, 2),
        "potential_gain_per_share": round(potential_gain_per_share, 2),
        "risk_reward_ratio": f"1:{round(rr_ratio, 2)}",
        "verdict": "Favorable" if rr_ratio >= 2 else "High Risk / Low Reward"
    }


@tool
def get_investment_params() -> dict:
    """
    Retrieve the current investment parameters (ticker, budget/amount, and max loss percentage).
    Check this first before performing any calculations or giving specific advice.
    """
    return _memory_store


@tool
def update_investment_params(ticker: str = None, amount: float = None, loss_pct: float = None) -> str:
    """
    Update the user's investment parameters. Only provide the fields that need to be changed.
    For example, if the user says "change amount to 20000", only provide amount=20000.
    """
    if ticker: _memory_store["ticker"] = ticker.upper()
    if amount is not None: _memory_store["amount"] = amount
    if loss_pct is not None: _memory_store["loss_pct"] = loss_pct
    return f"Parameters updated: {_memory_store}"



# 更新你的 tools 列表
tools = [
    get_current_quote, 
    get_company_profile, 
    get_recent_news, 
    calculate_position_size,
    get_investment_params,      
    update_investment_params   
]




