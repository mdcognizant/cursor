#!/usr/bin/env python3
"""
Claude Response Helper
This script allows Claude (me) to respond to user messages in real-time
"""

import requests
import json
import sys

def respond_to_message(message_id: str, response: str, backend_url: str = "http://localhost:8004"):
    """Send Claude's response to a user message"""
    
    try:
        url = f"{backend_url}/claude-chat/respond"
        data = {
            "message_id": message_id,
            "response": response
        }
        
        print(f"📤 Sending Claude response to message {message_id}")
        print(f"💬 Response: {response[:100]}...")
        
        response_obj = requests.post(url, json=data)
        
        if response_obj.status_code == 200:
            result = response_obj.json()
            if result.get("status") == "success":
                print("✅ Response sent successfully!")
                return True
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response_obj.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def get_pending_messages(backend_url: str = "http://localhost:8004"):
    """Get list of pending messages waiting for Claude"""
    try:
        # This would require an additional endpoint to list pending messages
        # For now, we'll use the conversation history endpoint
        url = f"{backend_url}/claude-chat/conversation"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("conversation", [])
        else:
            print(f"❌ Failed to get conversation: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Exception getting conversation: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python claude_responder.py <message_id> <response>")
        print("Example: python claude_responder.py claude_msg_123456789 'Hello! I can help you with that.'")
        sys.exit(1)
    
    message_id = sys.argv[1]
    response_text = sys.argv[2]
    
    success = respond_to_message(message_id, response_text)
    sys.exit(0 if success else 1) 