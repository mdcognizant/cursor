from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import requests
import json
import os

app = FastAPI(title="Simple Monerium Backend Gateway")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# OpenAI configuration
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Monerium configuration
MONERIUM_CLIENT_ID = "your_client_id"
MONERIUM_CLIENT_SECRET = "your_client_secret"
MONERIUM_API_BASE = "https://api.monerium.app"

def parse_intent(message: str) -> str:
    """Determine if message is for Monerium API or general LLM chat."""
    message_lower = message.lower()
    
    monerium_keywords = [
        "balance", "send", "transfer", "iban", "wallet", 
        "monerium", "payment", "withdraw", "deposit"
    ]
    
    for keyword in monerium_keywords:
        if keyword in message_lower:
            return "monerium"
    
    return "llm"

async def call_openai(message: str) -> str:
    """Call OpenAI API directly."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI API error: {str(e)}"

async def call_monerium_api(message: str) -> str:
    """Handle Monerium API calls."""
    try:
        # For demo purposes, return mock responses
        if "balance" in message.lower():
            return "Mock Monerium Response: Your balance is £1,000.00 GBPe"
        elif "transfer" in message.lower():
            return "Mock Monerium Response: Transfer initiated. Check your dashboard for details."
        elif "iban" in message.lower():
            return "Mock Monerium Response: Your IBAN is GB29 1234 5678 9012 3456"
        else:
            return "Mock Monerium Response: Available commands - balance, transfer, iban"
    except Exception as e:
        return f"Monerium API error: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Simple chat endpoint that calls APIs directly."""
    try:
        user_message = request.message
        intent = parse_intent(user_message)
        
        if intent == "monerium":
            response_text = await call_monerium_api(user_message)
        else:
            response_text = await call_openai(user_message)
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Simple Backend Gateway is running"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple Monerium Backend Gateway...")
    print("🌐 Backend Gateway: localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 
