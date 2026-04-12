"""

uvicorn api:app --reload

"""



from fastapi import FastAPI
from pydantic import BaseModel
# Import the function from your teammates' file
from agent_runner import run_investment_agent

app = FastAPI()

# Define what the frontend will send
class InvestmentRequest(BaseModel):
    user_input: str

# Define the endpoint
@app.post("/api/invest")
def get_investment_advice(request: InvestmentRequest):
    try:
        # Call their agent with the user's string
        advice = run_investment_agent(request.user_input)
        # Return the string wrapped in JSON
        return {"reply": advice}
    except Exception as e:
        return {"reply": f"Error communicating with agent: {str(e)}"}