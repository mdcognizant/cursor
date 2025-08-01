#!/usr/bin/env python3
"""
Process Monerium Request File

Usage: python process_monerium_request.py <request_file.json>

This script processes a single request file and generates a response file.
No localhost or network communication required.
"""

import sys
import json
from openai import OpenAI
import os
from pathlib import Path

class MoneriumRequestProcessor:
    def __init__(self):
        # OpenAI configuration
        self.openai_api_key = "YOUR_OPENAI_API_KEY_HERE"
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        print("🚀 Monerium Request Processor initialized")
        print("🔑 OpenAI API configured")
    
    def parse_intent(self, message: str) -> str:
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
    
    def call_openai(self, message: str) -> str:
        """Call OpenAI API directly."""
        try:
            print("🧠 Calling OpenAI API...")
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            result = response.choices[0].message.content
            print("✅ OpenAI API response received")
            return result
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def call_monerium_api(self, message: str) -> str:
        """Handle Monerium API calls (simulated for demo)."""
        try:
            print("🏦 Processing Monerium request...")
            
            if "balance" in message.lower():
                result = "Your current balance is £1,247.83 GBPe. Last updated: Today 2:30 PM"
            elif "transfer" in message.lower():
                result = "Transfer request received. To complete: specify amount and recipient IBAN. Example: 'transfer £100 to GB29 1234 5678 9012 3456'"
            elif "iban" in message.lower():
                result = "Your Monerium IBAN: GB29 MNRM 1234 5678 9012 3456 (Bank: Monerium, Currency: GBPe)"
            elif "send" in message.lower():
                result = "Send money feature available. Specify: amount, recipient IBAN, and reference. Processing time: 1-2 business days."
            elif "deposit" in message.lower():
                result = "To deposit: Send GBP to your IBAN GB29 MNRM 1234 5678 9012 3456. Reference: Your wallet address."
            elif "withdraw" in message.lower():
                result = "Withdrawal options: 1) Bank transfer to linked account, 2) Convert to other currencies. Min: £10, Max: £10,000/day"
            else:
                result = "Monerium services available: balance, transfer, iban, send, deposit, withdraw. How can I help you today?"
            
            print("✅ Monerium response generated")
            return result
            
        except Exception as e:
            error_msg = f"Monerium API error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def process_request(self, request_file: str) -> str:
        """Process a request file and generate response file."""
        request_path = Path(request_file)
        
        if not request_path.exists():
            print(f"❌ Request file not found: {request_file}")
            return None
        
        try:
            # Read request
            print(f"📥 Reading request file: {request_path.name}")
            with open(request_path, 'r') as f:
                request_data = json.load(f)
            
            message = request_data.get('message', '')
            request_id = request_data.get('id', 'unknown')
            
            print(f"📨 Message: {message}")
            print(f"🆔 Request ID: {request_id}")
            
            # Determine intent and process
            intent = self.parse_intent(message)
            print(f"🎯 Intent: {intent}")
            
            if intent == "monerium":
                response = self.call_monerium_api(message)
            else:
                response = self.call_openai(message)
            
            # Generate response file
            response_filename = f"monerium_response_{request_id}.json"
            response_path = request_path.parent / response_filename
            
            response_data = {
                "request_id": request_id,
                "original_message": message,
                "response": response,
                "intent": intent,
                "timestamp": request_data.get('timestamp'),
                "processed_at": int(time.time() * 1000) if 'time' in sys.modules else request_data.get('timestamp')
            }
            
            with open(response_path, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            print(f"📤 Response saved: {response_path.name}")
            print(f"✅ Processing complete!")
            
            return str(response_path)
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_monerium_request.py <request_file.json>")
        print("Example: python process_monerium_request.py monerium_request_1.json")
        return
    
    request_file = sys.argv[1]
    processor = MoneriumRequestProcessor()
    
    response_file = processor.process_request(request_file)
    if response_file:
        print(f"\n🎉 Success! Upload {Path(response_file).name} to the HTML interface.")
    else:
        print("\n💥 Failed to process request.")

if __name__ == "__main__":
    import time
    main() 
