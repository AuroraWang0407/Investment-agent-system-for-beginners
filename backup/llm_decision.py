import json
import re
from langchain_openai import ChatOpenAI

# 1. Initialize LLM
def get_llm():
    return ChatOpenAI(
        api_key="sk-f60bcfd440ce484ebada95ba4d6bc7d1",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="deepseek-v3.2",
        temperature=0.0
    )

llm = get_llm()

# 2. Memory Module (persisted across multi-round conversations)
class AgentMemory:
    def __init__(self):
        self.data = {
            "ticker": None,
            "amount": None,
            "loss_pct": None,
            "tool_results": None
        }

    def update(self, key, value):
        if value is not None:
            self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def get_all(self):
        return self.data.copy()

    def has_basic_info(self):
        """Check if all basic investment information is complete"""
        return all([self.data["ticker"], self.data["amount"], self.data["loss_pct"]])

# 3. [Super Enhanced] Parsing Function - Resolve JSON Parsing Failures
def parse_user_input(user_input: str, memory: AgentMemory):
    history = memory.get_all()
    h_ticker = history["ticker"] or "Not Set"
    h_amount = history["amount"] or "Not Set"
    h_loss = history["loss_pct"] or "Not Set"

    prompt = f'''
        INSTRUCTIONS:
        1. Output ONLY pure JSON format, with no additional text, explanations, line breaks, or markdown formatting
        2. Extract exactly three fields from user input:
        - ticker: Stock ticker symbol (string, e.g., GOOGL, MSFT)
        - amount: Investment amount (numeric value, USD, no currency symbols)
        - loss_pct: Stop loss percentage (numeric value, percentage points, e.g., 5 for 5%)
        3. For fields not mentioned in the current user input, use historical values to fill
        4. Historical values reference:
        - ticker: {h_ticker}
        - amount: {h_amount}
        - loss_pct: {h_loss}
        5. If historical value is "Not Set" and current input doesn't specify, keep it as null (but maintain JSON structure)
        6. Ensure amount and loss_pct are pure numeric values (no strings, no commas, no currency symbols)

        OUTPUT FORMAT (strict):
        {{"ticker":"STRING_VALUE","amount":NUMERIC_VALUE,"loss_pct":NUMERIC_VALUE}}

        USER INPUT: {user_input}
    '''

    # Call LLM
    res = llm.invoke(prompt).content.strip()

    # ==============================================
    # [Strongest Cleaning] Force extract JSON structure
    # ==============================================
    res = re.sub(r'```json|```', '', res)
    res = re.sub(r'\s+', ' ', res)  # Replace all whitespace with single space
    match = re.search(r'(\{.*\})', res)
    if match:
        res = match.group(1)

    # Parse JSON
    try:
        data = json.loads(res)
    except Exception as e:
        raise ValueError(f"LLM returned invalid format: {res[:100]}...")

    # Incremental update memory
    ticker = data.get("ticker")
    amount = data.get("amount")
    loss_pct = data.get("loss_pct")

    if ticker and ticker != "Not Set":
        memory.update("ticker", str(ticker))
    if amount and amount != "Not Set":
        memory.update("amount", float(amount))
    if loss_pct and loss_pct != "Not Set":
        memory.update("loss_pct", float(loss_pct))

    return memory


# 4. Generate tool commands
def generate_tool_commands(memory: AgentMemory, invest_tools: dict):
    """Generate standardized tool execution commands based on memory data"""
    ticker = memory.get("ticker")
    if not ticker:
        raise ValueError("Stock ticker is missing")
    cmds = []
    for name in invest_tools:
        cmds.append({"tool": name, "params": {"ticker": ticker}})
    return cmds


# 5. Generate investment advice
def generate_investment_advice(memory: AgentMemory):
    """Generate clear, actionable investment advice based on market data and user parameters"""
    data = memory.get_all()
    ticker = data["ticker"]
    amount = data["amount"]
    loss_pct = data["loss_pct"]
    tools = data["tool_results"]

    price = tools["get_stock_data"]["current_price"]
    news = tools["get_stock_news"]["news_list"]

    # Calculate key investment metrics
    shares = round(amount / price, 2) if price > 0 else 0
    stop_loss_price = round(price * (1 - loss_pct / 100), 2) if price > 0 else 0

    prompt = f'''
        You are a professional stock investment advisor with extensive experience in US stock markets.
        Your task is to provide clear, concise, and actionable investment advice based on the following data:

        CORE INVESTMENT PARAMETERS:
        - Stock Ticker: {ticker}
        - Current Stock Price: ${price} USD
        - Investment Amount: ${amount} USD
        - Maximum Acceptable Loss: {loss_pct}% (stop loss)
        - Calculated Shares to Buy: {shares} shares
        - Stop Loss Trigger Price: ${stop_loss_price} USD

        LATEST RELEVANT NEWS (top 5 items):
        {json.dumps(news, indent=2)}

        ADVICE REQUIREMENTS:
        1. Start with a clear recommendation: "Recommended to buy" OR "Not recommended to buy"
        2. Provide 2-3 key reasons (based on price data and news sentiment)
        3. Include strict stop loss discipline reminder (emphasize following the stop loss price)
        4. Use simple, plain English (avoid financial jargon)
        5. Keep the advice concise (3-4 sentences maximum)
        6. Do not include any markdown formatting or extra symbols
'''
    return llm.invoke(prompt).content