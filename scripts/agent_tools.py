"""
工具清单，可供 llm 自行选择
改用官方 API：Finnhub (行情) + Alpha Vantage (新闻/情绪/公司信息)
"""

import os
import requests
from langchain_classic.agents import tool

# 显式内存：存储当前会话的参数
_memory_store = {
    "ticker": "None",
    "amount": 0.0,
    "loss_pct": 8.0  # 默认值
}

# ===== API KEY 管理 =====
def get_api_key(key_name: str) -> str:
    """
    获取 API key，优先从 Streamlit secrets（Streamlit 环境），备用 .env（本地环境）
    """
    # 首先尝试从 Streamlit secrets 获取（仅在 Streamlit 运行时有效）
    try:
        import streamlit as st
        # 检查是否在 Streamlit 环境中
        if hasattr(st, 'secrets'):
            key = st.secrets.get(key_name)
            if key and key != "":
                return key
    except:
        # 不在 Streamlit 环境，继续使用 .env
        pass
    
    # 备用：从 .env 文件或环境变量获取（本地环境）
    key = os.getenv(key_name, "").strip()
    if key:
        return key
    
    # 都没有则返回空（会在调用时被检查）
    return ""


# ===== 1. Finnhub API - 实时股票报价 =====
@tool
def get_current_quote(ticker: str) -> dict:
    """
    Fetch the latest real-time quote for a stock ticker using Finnhub API.
    Returns current price, change, volume, day's range, etc.
    Useful for beginners who want to know the current price quickly.
    """
    try:
        api_key = get_api_key("FINNHUB_API_KEY")
        if not api_key:
            return {
                "ticker": ticker.upper(),
                "error": "Finnhub API key not found. Please configure FINNHUB_API_KEY in .env or Streamlit secrets."
            }
        
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker.upper()}&token={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "c" not in data:
            return {
                "ticker": ticker.upper(),
                "error": "Invalid ticker symbol or no data available"
            }
        
        quote = {
            "ticker": ticker.upper(),
            "current_price": data.get("c"),  # current price
            "previous_close": data.get("pc"),  # previous close
            "change": round(data.get("c", 0) - data.get("pc", 0), 2),
            "change_percent": round(((data.get("c", 0) - data.get("pc", 0)) / data.get("pc", 1) * 100), 2) if data.get("pc") else None,
            "day_high": data.get("h"),  # day high
            "day_low": data.get("l"),  # day low
            "open": data.get("o"),  # open
            "volume": "N/A",  # Finnhub free plan 不提供 volume
            "currency": "USD",
            "market_state": "Unknown",
        }
        
        return quote
        
    except requests.exceptions.Timeout:
        return {"ticker": ticker.upper(), "error": "Request timeout - Finnhub API unavailable"}
    except requests.exceptions.RequestException as e:
        return {"ticker": ticker.upper(), "error": f"Failed to fetch from Finnhub: {str(e)}"}
    except Exception as e:
        return {"ticker": ticker.upper(), "error": f"Failed to fetch quote: {str(e)}"}


# ===== 2. Alpha Vantage - 公司信息 + 新闻情绪 =====
@tool
def get_company_profile(ticker: str) -> dict:
    """
    Get company information and market sentiment using Alpha Vantage NEWS_SENTIMENT API.
    Returns company name, sentiment analysis, top news themes.
    """
    try:
        api_key = get_api_key("ALPHAVANTAGE_API_KEY")
        if not api_key:
            return {
                "ticker": ticker.upper(),
                "error": "Alpha Vantage API key not found. Please configure ALPHAVANTAGE_API_KEY in .env or Streamlit secrets."
            }
        
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker.upper()}&apikey={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "items" not in data or not data.get("items"):
            return {
                "ticker": ticker.upper(),
                "error": "No data available or API rate limit reached. Try again later."
            }
        
        # 提取公司信息和情绪数据
        items = data.get("items", [])
        ticker_sentiment = data.get("ticker_sentiment", [])
        
        # 找主要的 ticker 情绪
        main_sentiment = None
        if ticker_sentiment:
            for sentiment in ticker_sentiment:
                if sentiment.get("ticker") == ticker.upper():
                    main_sentiment = sentiment
                    break
        
        profile = {
            "ticker": ticker.upper(),
            "company_name": ticker.upper(),  # Alpha Vantage 不提供公司名，用 ticker 代替
            "sentiment": main_sentiment.get("ticker_sentiment_score", "N/A") if main_sentiment else "N/A",
            "sentiment_label": main_sentiment.get("ticker_sentiment_label", "N/A") if main_sentiment else "N/A",
            "relevant_news_count": len(items),
            "top_news_title": items[0].get("title", "N/A") if items else "N/A",
            "top_news_url": items[0].get("url", "N/A") if items else "N/A",
            "business_summary": f"Latest news sentiment: {main_sentiment.get('ticker_sentiment_label', 'Unknown')} " 
                               if main_sentiment else "No sentiment data available",
        }
        
        return profile
        
    except requests.exceptions.Timeout:
        return {"ticker": ticker.upper(), "error": "Request timeout - Alpha Vantage API unavailable"}
    except requests.exceptions.RequestException as e:
        return {"ticker": ticker.upper(), "error": f"Failed to fetch from Alpha Vantage: {str(e)}"}
    except Exception as e:
        return {"ticker": ticker.upper(), "error": f"Failed to fetch company profile: {str(e)}"}


# ===== 3. NewsAPI - 新闻和情绪分析 =====
@tool
def get_recent_news(ticker: str, limit: int = 5) -> dict:
    """
    Retrieves the latest stock news using NewsAPI.org.
    Returns news articles with basic sentiment analysis.
    """
    try:
        api_key = get_api_key("NEWSAPI_API_KEY")
        if not api_key:
            return {
                "ticker": ticker.upper(),
                "error": "NewsAPI key not found. Please configure NEWSAPI_API_KEY in .env or Streamlit secrets."
            }
        
        # 使用公司名称进行搜索（更准确）
        company_names = {
            "NVDA": "NVIDIA",
            "TSLA": "Tesla",
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "AMZN": "Amazon",
            "META": "Meta",
            "NFLX": "Netflix"
        } 
        
        search_term = company_names.get(ticker.upper(), ticker.upper())
        url = f"https://newsapi.org/v2/everything?q={search_term}&sortBy=publishedAt&language=en&apiKey={api_key}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok" or not data.get("articles"):
            return {
                "ticker": ticker.upper(),
                "error": "No news available or API rate limit reached. Try again later.",
                "news_source": "NewsAPI"
            }
        
        # 解析新闻
        articles = data.get("articles", [])[:limit]
        news_list = []
        for article in articles:
            # 简单的情绪分析（基于标题关键词）
            title = article.get("title", "").lower()
            sentiment = "NEUTRAL"
            if any(word in title for word in ["rise", "up", "gain", "bull", "positive", "growth", "profit"]):
                sentiment = "POSITIVE"
            elif any(word in title for word in ["fall", "down", "loss", "bear", "negative", "decline", "drop"]):
                sentiment = "NEGATIVE"
            
            news_list.append({
                "title": article.get("title", "N/A"),
                "url": article.get("url", "N/A"),
                "publishedAt": article.get("publishedAt", "N/A"),
                "source": article.get("source", {}).get("name", "N/A"),
                "sentiment": sentiment,
            })
        
        # 计算整体情绪
        positive_count = sum(1 for n in news_list if n["sentiment"] == "POSITIVE")
        negative_count = sum(1 for n in news_list if n["sentiment"] == "NEGATIVE")
        
        if positive_count > negative_count:
            overall_sentiment = "POSITIVE"
        elif negative_count > positive_count:
            overall_sentiment = "NEGATIVE"
        else:
            overall_sentiment = "NEUTRAL"
        
        return {
            "ticker": ticker.upper(),
            "news_source": "NewsAPI",
            "overall_sentiment": overall_sentiment,
            "total_articles": len(news_list),
            "news_articles": news_list,
            "raw_news": "\n".join([f"- {n['title']} ({n['sentiment']})" for n in news_list])[:3000],
            "note": f"Overall market sentiment for {ticker.upper()}: {overall_sentiment}. Please summarize based on the articles above."
        }
        
    except requests.exceptions.Timeout:
        return {
            "ticker": ticker.upper(),
            "error": "Request timeout - NewsAPI unavailable",
            "news_source": "NewsAPI"
        }
    except requests.exceptions.RequestException as e:
        return {
            "ticker": ticker.upper(),
            "error": f"Failed to fetch from NewsAPI: {str(e)}",
            "news_source": "NewsAPI"
        }
    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "error": f"Failed to fetch recent news: {str(e)}",
            "news_source": "NewsAPI"
        }


# ===== 其他工具（保持不变）=====
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
    analyze_risk_reward,
    get_investment_params,      
    update_investment_params   
]
