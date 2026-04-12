import json
from wky.llm_decision import AgentMemory, parse_user_input, generate_tool_commands, generate_investment_advice
from wky.agent_executor import execute_tool_commands


def main():
    # Initialize memory (persisted across multiple rounds)
    memory = AgentMemory()
    print("===== Stock Investment Analysis Assistant =====")
    print(" Support multi-round modification of investment requirements. Input examples:")
    print("   - Initial input: Invest $20000 in GOOGL, sell if loss reaches 5%")
    print("   - Incremental modification: Change the amount to $30000")
    print("   - Incremental modification: Switch to MSFT with 8% stop loss")
    print("   - Exit commands: Enter 'exit', 'quit', 'q' to exit\n")

    while True:
        # Step 1: User input (support exit)
        user_input = input("Please enter your investment requirements (or exit commands to end): ").strip()
        # Exit mechanism
        if user_input.lower() in ["exit", "quit", "q", "结束", "退出"]:
            print(" Thank you for using the assistant! Wish you profitable investments!")
            break
        if not user_input:
            print(" Input cannot be empty! Please try again.")
            continue

        try:
            # Step 2: Parse requirements (incremental update, retain historical values)
            memory = parse_user_input(user_input, memory)
            # Check if basic three elements are complete
            if not memory.has_basic_info():
                missing_fields = []
                if not memory.get("ticker"):
                    missing_fields.append("Stock Ticker")
                if not memory.get("amount"):
                    missing_fields.append("Investment Amount")
                if not memory.get("loss_pct"):
                    missing_fields.append("Stop Loss Percentage")
                print(f" Core information missing: {','.join(missing_fields)}. Please complete the information!")
                continue
            print(f"\n===== Parsed User Input (Latest Parameters) =====\n{json.dumps(memory.get_all(), indent=2)}")

            # Step 3: Generate tool commands
            commands = generate_tool_commands(memory)
            print(f"\n===== Generated Tool Commands =====\n{json.dumps(commands, indent=2)}")

            # Step 4: Execute tool commands
            if commands: 
                tool_results = execute_tool_commands(commands)
                memory.update("tool_results", tool_results)
            else:
                tool_results = {} 

            print(f"\n===== Tool Execution Results =====\n{json.dumps(tool_results, indent=2)}")

            # Step 5: Generate investment advice
            advice = generate_investment_advice(memory)
            print("\n===== Investment Advice =====")
            print(advice)
            print("\n" + "-"*50 + "\n")  # Separator for better readability

        except Exception as e:
            print(f"\n Processing failed: {str(e)}")
            print("Please check your input format and try again!\n")
            continue


if __name__ == "__main__":
    main()