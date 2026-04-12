import streamlit as st
import requests
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# Set page config
st.set_page_config(page_title="智能股票投资助手 / AI Stock Assistant", page_icon="📈", layout="wide")

# Set default language to English
if "language" not in st.session_state:
    st.session_state.language = "en"

# -----------------------------------------
# 1. Fetch Real Market Data Function
# -----------------------------------------
@st.cache_data(ttl=30)  
def get_market_data():
    tickers = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "GOLD": "GC=F", "VIX (Volatility Index)": "^VIX"}
    market_data = {}
    
    for name, ticker_symbol in tickers.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            # 5d ensures we always have enough data, even over long holiday weekends
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                pct_change = ((current_price - prev_price) / prev_price) * 100
                market_data[name] = {
                    "price": current_price,
                    "change": pct_change
                }
            else:
                market_data[name] = None
        except Exception:
            market_data[name] = None
            
    # Set display timezone to Hong Kong
    local_tz = pytz.timezone('Asia/Hong_Kong')
    fetch_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    return market_data, fetch_time

# -----------------------------------------
# 2. Fetch Trending Stocks Data
# -----------------------------------------
@st.cache_data(ttl=30)  
def get_trending_stocks():
    trending_tickers = {"NVIDIA": "NVDA", "Tesla": "TSLA", "Palantir": "PLTR", "MicroStrategy": "MSTR"}
    trending_data = {}
    
    for name, ticker_symbol in trending_tickers.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d") 
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                pct_change = ((current_price - prev_price) / prev_price) * 100
                trending_data[name] = {
                    "price": current_price,
                    "change": pct_change
                }
            else:
                trending_data[name] = None
        except Exception:
            trending_data[name] = None
            
    return trending_data

# -----------------------------------------
# 3. Market Time Logic (US Eastern Time)
# -----------------------------------------
def get_market_status(t):
    ny_tz = pytz.timezone('US/Eastern')
    now_ny = datetime.now(ny_tz)
    
    market_open_time = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close_time = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    
    weekday = now_ny.weekday()
    
    if weekday < 5 and market_open_time <= now_ny <= market_close_time:
        diff = market_close_time - now_ny
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"🟢 **{t['market_open']}** ({t['closes_in']} {hours}h {minutes}m)"
    
    else:
        next_open = market_open_time
        if now_ny > market_close_time or weekday >= 5:
            next_open += timedelta(days=1)
            
        while next_open.weekday() >= 5:
            next_open += timedelta(days=1)
            
        diff = next_open - now_ny
        total_seconds = int(diff.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if diff.days > 0:
            return f"🔴 **{t['market_closed']}** ({t['opens_in']} {diff.days}d {hours}h {minutes}m)"
        else:
            return f"🔴 **{t['market_closed']}** ({t['opens_in']} {hours}h {minutes}m)"

# -----------------------------------------
# 4. UI Text Dictionary 
# -----------------------------------------
ui_text = {
    "zh": {
        "header": "📈 智能股票投资助手",
        "welcome": "欢迎！请告诉我您的**投资金额**、**意向股票**，以及**最大可接受的亏损比例**。",
        "chat_placeholder": "例如：我想投10000块买AAPL，最多亏15%",
        "spinner": "AI正在分析最新新闻和市场数据，请稍候...",
        "error_conn": "⚠️ API连接失败。请确保后端的 FastAPI 服务正在运行！",
        "error_unknown": "发生未知错误: ",
        "sidebar_title": "⚙️ 控制面板",
        "clear_chat": "🗑️ 清空对话",
        "disclaimer": "⚠️ **免责声明**: 本系统为课程测试项目。所提供建议不构成真实的财务或投资建议。",
        "market_overview": "🌐 全球市场概览",
        "last_updated": "最后更新",
        "refresh_btn": "手动刷新",
        "market_open": "美股交易中",
        "market_closed": "美股已休市",
        "opens_in": "距开盘:",
        "closes_in": "距收盘:",
        "trending_title": "🔥 热门关注"
    },
    "en": {
        "header": "📈 AI Stock Investment Assistant",
        "welcome": "Welcome! Please tell me your **investment amount**, **target stock**, and **maximum acceptable loss percentage**.",
        "chat_placeholder": "e.g., I want to invest $10000 in AAPL, max loss 15%",
        "spinner": "AI is analyzing the latest news and market data...",
        "error_conn": "⚠️ API connection failed. Please ensure the backend FastAPI service is running!",
        "error_unknown": "An unknown error occurred: ",
        "sidebar_title": "⚙️ Control Panel",
        "clear_chat": "🗑️ Clear Chat",
        "disclaimer": "⚠️ **Disclaimer**: This system is a course project. Advice is simulated and does NOT constitute real financial advice.",
        "market_overview": "🌐 Global Market Overview",
        "last_updated": "Last updated",
        "refresh_btn": "Refresh",
        "market_open": "US Market Open",
        "market_closed": "US Market Closed",
        "opens_in": "Opens in:",
        "closes_in": "Closes in:",
        "trending_title": "🔥 Trending Stocks"
    }
}

# Custom CSS (Header is kept visible so sidebar button remains)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;}    
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# -----------------------------------------
# 5. Top Header Area
# -----------------------------------------
col_title, col_lang = st.columns([8, 2])

with col_lang:
    # CHANGED: Replaced radio buttons with a selectbox (dropdown list)
    # The label "Language / 语言" is now fully visible above the list!
    lang_choice = st.selectbox(
        "Language / 语言", 
        options=["中文", "English"],
        index=0 if st.session_state.language == "zh" else 1
    )
    
    new_lang = "zh" if lang_choice == "中文" else "en"
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun() 

t = ui_text[st.session_state.language]

with col_title:
    st.title(t["header"])

st.markdown(t["welcome"])

# -----------------------------------------
# 6. REAL-TIME Auto-Updating Market Metrics
# -----------------------------------------
@st.fragment(run_every=30)
def display_live_market_data():
    col_text, col_btn = st.columns([9, 1])
    
    with col_btn:
        if st.button("🔄 " + t["refresh_btn"], use_container_width=True):
            get_market_data.clear()
            get_trending_stocks.clear()
            
    market_stats, fetch_time = get_market_data()
    trending_stats = get_trending_stocks()
    status_msg = get_market_status(t)
    
    # We move the status caption to the top so it spans the whole screen
    st.caption(f"{status_msg} &nbsp;|&nbsp; ⏱️ {t['last_updated']}: **{fetch_time}**")
    
    # CHANGED: Create 3 columns - Left (48%), Middle Line (4%), Right (48%)
    col_global, col_line, col_trend = st.columns([48, 4, 48])
    
    # --- LEFT SIDE: GLOBAL MARKET ---
    with col_global:
        st.markdown(f"#### {t['market_overview']}") 
        # Nest columns inside the left half
        cols_market = st.columns(len(market_stats))
        for i, (name, data) in enumerate(market_stats.items()):
            with cols_market[i]:
                if data is not None:
                    if "GOLD" in name or "S&P" in name or "NASDAQ" in name:
                        price_str = f"{data['price']:,.2f}"
                    else: 
                        price_str = f"{data['price']:.2f}"
                    st.metric(label=name, value=price_str, delta=f"{data['change']:.2f}%")
                else:
                    st.metric(label=name, value="N/A", delta="N/A")
                    
    # --- MIDDLE: VERTICAL LINE ---
    with col_line:
        # A simple HTML/CSS trick to draw a subtle vertical separator
        st.markdown(
            """
            <div style="
                border-left: 1.5px solid rgba(128, 128, 128, 0.3); 
                height: 100px; 
                margin: 20px auto 0px auto; 
                width: 1px;">
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    # --- RIGHT SIDE: TRENDING STOCKS ---
    with col_trend:
        st.markdown(f"#### {t['trending_title']}")
        # Nest columns inside the right half
        cols_trending = st.columns(len(trending_stats))
        for i, (name, data) in enumerate(trending_stats.items()):
            with cols_trending[i]:
                if data is not None:
                    st.metric(label=name, value=f"${data['price']:.2f}", delta=f"{data['change']:.2f}%")
                else:
                    st.metric(label=name, value="N/A", delta="N/A")
                    
    # Keep one single horizontal divider at the very bottom
    st.divider()

display_live_market_data()

# -----------------------------------------
# 7. Sidebar (Tools & Disclaimers)
# -----------------------------------------
with st.sidebar:
    st.header(t["sidebar_title"])
    
    if st.button(t["clear_chat"], use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    
    with st.expander("ℹ️ 关于系统 / About"):
        st.caption(t["disclaimer"])

# -----------------------------------------
# 8. Chat Interface
# -----------------------------------------
USER_AVATAR = "🧑‍💻"
BOT_AVATAR = "📊"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input(t["chat_placeholder"]):
    st.chat_message("user", avatar=USER_AVATAR).markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner(t["spinner"]):
        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/invest", 
                json={"user_input": prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                bot_reply = response.json().get("reply", "Agent failed to return a message.")
            else:
                bot_reply = f"Error {response.status_code}: {t['error_conn']}"
                
        except requests.exceptions.ConnectionError:
            bot_reply = t["error_conn"]
        except Exception as e:
            bot_reply = f"{t['error_unknown']} {str(e)}"

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})