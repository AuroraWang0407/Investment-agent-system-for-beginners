
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith.schemas import Run, Example
import json

# Load environment variables
load_dotenv()

judge_llm = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    temperature=float(os.getenv("EVAL_TEMPERATURE", 0.0)))



def tool_calling_evaluator(run: Run, example: Example = None):
    """
    Advanced evaluator:
    1. Use LLM to classify the question as general or investment-related
    2. Use code to check tool call count
    3. Use LLM to verify that answers are factual and free of hallucinations
    """

    # ========== 1. Extract data from run (core strength of code) ==========
    user_input = run.inputs.get("input", "")
    agent_output = run.outputs.get("output", "")
    intermediate_steps = run.outputs.get("intermediate_steps", [])
    tool_call_count = len(intermediate_steps)

    # ========== 2. LLM classification of question type ==========
    type_prompt = f"""
    User question: {user_input}
    Classify into one category:
    - general: investment knowledge, beginner tips, methods, principles, no real-time data required
    - investment: involves specific stocks, requires price, news, data, or concrete trading advice, or comparing two stocks
    Output only: general or investment
    """
    q_type = judge_llm.invoke(type_prompt).content.strip()

    # ========== 3. Evaluation logic ==========
    score = 0
    reason = ""

    if q_type == "general":
        # General question → must NOT call tools
        if tool_call_count == 0:
            score = 1
            reason = "General question, no tools called"
        else:
            score = 0
            reason = f"General question but tools were called {tool_call_count} times"

    else:
        # Investment question → must call tools > 1 times AND answer must be factual
        if tool_call_count <= 1:
            score = 0
            reason = f"Insufficient tool calls for investment question ({tool_call_count} times)"
        else:
            # Collect tool outputs
            tool_texts = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    tool_texts.append(str(step[1]))
            tool_all_text = "\n".join(tool_texts)

            # LLM fact-checking
            fact_check_prompt = f"""
            Tool output information:
            {tool_all_text}

            Agent response:
            {agent_output}

            Determine: Is the agent response fully based on the tool information with no fabrication, hallucination, or speculation?
            Output only: true or false
            """
            is_factual = judge_llm.invoke(fact_check_prompt).content.strip()

            if is_factual == "true":
                score = 1
                reason = f"Investment question, {tool_call_count} tool calls, response is factual"
            else:
                score = 0
                reason = "Investment question, but response contains fabrication or hallucination"

    return {
        "key": "tool_usage_ability",
        "score": score,
    }


def calculate_final_score(run: Run, example: Example = None):
    """
    Weighted final score calculator for 4 metrics
    tool_usage_ability: 0.3
    safe_compliance: 0.2
    answer_relevance: 0.3
    hallucination: 0.2
    """

    # FIXED: Correct way to get scores in LangSmith
    feedback = run.feedback or []
    score_map = {}
    
    for fb in feedback:
        key = fb.key
        score = fb.score
        if score is not None:
            score_map[key] = score

    # Get each score (default 0)
    tool_usage = score_map.get("tool_usage_ability", 0)
    safe_comp = score_map.get("safe_compliance", 0)
    relevance = score_map.get("answer_relevance", 0)
    hallucination = score_map.get("hallucination", 0)

    # Weighted calculation
    final = (
        tool_usage * 0.3 +
        safe_comp * 0.2 +
        relevance * 0.3 +
        hallucination * 0.2
    )

    return {
        "key": "final_score",
        "score": round(final, 2),
    }