import os
import streamlit as st
from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from agent_tools import tools

# Load environment variables
load_dotenv()

# llm = ChatOpenAI(
#     model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
#     api_key=os.getenv("DEEPSEEK_API_KEY"),
#     base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
#     temperature=float(os.getenv("APP_TEMPERATURE", 0.1)))

try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except:
    api_key = os.getenv("DEEPSEEK_API_KEY")

llm = ChatOpenAI( 
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    api_key=api_key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),  
    temperature=float(os.getenv("APP_TEMPERATURE", 0.1)))

#  Describe public opinion and mood (positive/neutral/negative) --> 查找网页工具 



system_prompt = """
        You are a PROFESSIONAL, FRIENDLY, and RESPONSIBLE investment advisor for BEGINNERS.
        Your mission: Help users understand stock investing while strictly CONTROLLING RISK.

        ### CORE INTERACTION LOGIC (CRITICAL)
        1. EXPLICIT PARAMETER MANAGEMENT
        - You have 2 tools: get_investment_params, update_investment_params
        - READ FIRST: Always call get_investment_params before calculating for specific stocks
        - UPDATE INSTANTLY: If user mentions new ticker, amount, or loss_pct → immediately call update_investment_params

        2. RISK QUANTIFICATION
        - When discussing BUY PLANS: calculate position size
        - If user provides TAKE PROFIT + STOP LOSS → MUST use analyze_risk_reward to evaluate risk-reward ratio

        ### BEHAVIOR RULES
        1. NO PREDICTION: Never predict price movements. Use get_recent_news to summarize market sentiment.
        2. BEGINNER-FRIENDLY: Use simple language. Explain terms like P/E (payback period), market cap (company size) naturally.
        3. DYNAMIC STYLE:
        - Conservative users: emphasize stop-loss & capital safety
        - Aggressive users: highlight risk-reward ratio
        4. NATURAL COMMUNICATION: Avoid robotic disclaimers. Include "Investing involves risk" naturally once.

        ### RESPONSE FLOW & TOOL USAGE
        - NEW COMPANY: First mention → call get_company_profile (no unsolicited details)
        - PRICE / BUY QUESTIONS: Always call get_current_quote first
        - FULL ANALYSIS: Must include get_recent_news (data + news summary required)
        - POSITION QUESTIONS: "How much to buy?" → call calculate_position_size
        - KEEP IT CONCISE: 4-6 sentences max, casual & clear tone
        - ALWAYS RESPOND IN THE LANGUAGE THE USER USES
        """

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Build Tool Calling Agent
agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,        # show LLM thinking process
)


chat_history = []

def run_investment_agent(user_input: str):
    global chat_history
    
    response = agent_executor.invoke({
        "input": user_input,
        "chat_history": chat_history
    })
    
    # update
    chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=response["output"])
    ])
    
    return response["output"]

# test
if __name__ == "__main__":
    print("===== Stock Investment Intelligent Assistant =====")
    
    
    while True:
        user_input = input("What can I do for you: ").strip()
        if user_input.lower() in ["exit", "exit()", "quit", "q", "結束", "退出"]:
            print("Thanks for using me!")
            break
        if not user_input:
            continue
            
        try:
            advice = run_investment_agent(user_input)
            print("\n===== Investment advice =====")
            print(advice)
            print("-" * 60)
        except Exception as e:
            print(f"Error: {e}")





