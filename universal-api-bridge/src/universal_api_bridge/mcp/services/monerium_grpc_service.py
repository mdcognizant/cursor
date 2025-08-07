import grpc
from concurrent import futures
import json
import requests
import os
import sys

# Add the llm-agent-bridge directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'llm-agent-bridge'))

# Import the generated proto files (optional for testing)
try:
    import agent_service_pb2
    import agent_service_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    # Define minimal fallback classes
    class MockServicer:
        pass
    agent_service_pb2_grpc = type('MockModule', (), {
        'AgentCommunicationServiceServicer': MockServicer
    })()

# Monerium API Configuration
CLIENT_ID = os.environ.get("MONERIUM_CLIENT_ID") or "your_client_id"
CLIENT_SECRET = os.environ.get("MONERIUM_CLIENT_SECRET") or "your_client_secret"
PRIMARY_WALLET_ADDRESS = os.environ.get("MONERIUM_PRIMARY_WALLET") or "0xYourPrimaryWallet"
API_BASE_URL = "https://api.monerium.app"
CHAIN = "ethereum"
NETWORK = "sepolia"

class MoneriumService(agent_service_pb2_grpc.AgentCommunicationServiceServicer):
    def __init__(self):
        self.token = None
        self.profile_id = None
    
    def get_access_token(self):
        """Authenticate using the OAuth2 client_credentials flow."""
        url = f"{API_BASE_URL}/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    
    def get_profile_id(self, token):
        """Retrieve profile ID."""
        url = f"{API_BASE_URL}/auth/context"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["profiles"][0]
    
    def get_balance(self, token, wallet_address):
        """Check token balance for a wallet."""
        url = f"{API_BASE_URL}/balances/{CHAIN}/{wallet_address}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_ibans(self, token):
        """View all IBANs linked to account."""
        url = f"{API_BASE_URL}/ibans"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def place_order(self, token, profile_id, amount_gbp, to_wallet=None, to_iban=None, to_name=None):
        """Send money either to wallet or IBAN."""
        url = f"{API_BASE_URL}/orders"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if to_iban:
            counterpart = {
                "identifier": {"standard": "iban", "iban": to_iban},
                "details": {"name": to_name}
            }
        elif to_wallet:
            counterpart = {
                "identifier": {"standard": "wallet", "wallet": to_wallet},
                "details": {"name": to_name or "Wallet Transfer"}
            }
        else:
            raise ValueError("Must specify either to_iban or to_wallet.")
        
        data = {
            "amount": f"{amount_gbp:.2f}",
            "currency": "gbp",
            "chain": CHAIN,
            "network": NETWORK,
            "counterpart": counterpart,
            "message": "Internal transfer" if to_wallet else "Withdrawal to IBAN",
            "wallet": PRIMARY_WALLET_ADDRESS,
            "profile": profile_id,
            "signature": ""
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    
    def parse_intent(self, message):
        """Parse user message to determine Monerium operation."""
        message_lower = message.lower()
        
        if "balance" in message_lower:
            return "balance"
        elif "send" in message_lower or "transfer" in message_lower:
            return "transfer"
        elif "iban" in message_lower:
            return "ibans"
        else:
            return "unknown"
    
    def SendMessage(self, request, context):
        message = request.message.content
        intent = self.parse_intent(message)
        
        try:
            # Authenticate if needed
            if not self.token:
                self.token = self.get_access_token()
                self.profile_id = self.get_profile_id(self.token)
            
            if intent == "balance":
                balance = self.get_balance(self.token, PRIMARY_WALLET_ADDRESS)
                response_text = f"Your Monerium balance: {json.dumps(balance, indent=2)}"
            
            elif intent == "ibans":
                ibans = self.get_ibans(self.token)
                response_text = f"Your Monerium IBANs: {json.dumps(ibans, indent=2)}"
            
            elif intent == "transfer":
                # Simple transfer example (this could be enhanced with amount parsing)
                response_text = "Transfer functionality available. Please specify amount and destination."
            
            else:
                response_text = "I can help you with Monerium operations: check balance, view IBANs, or make transfers."
            
            return agent_service_pb2.SendMessageResponse(
                message_id="monerium-msg-1",
                response=agent_service_pb2.Message(
                    id="monerium-response-1",
                    content=response_text,
                    type=agent_service_pb2.MessageType.MESSAGE_TYPE_TEXT,
                    format="text"
                ),
                status=agent_service_pb2.MessageStatus.MESSAGE_STATUS_COMPLETED
            )
            
        except Exception as e:
            return agent_service_pb2.SendMessageResponse(
                message_id="monerium-err",
                response=agent_service_pb2.Message(
                    id="monerium-msg-err",
                    content=f"Monerium API error: {str(e)}",
                    type=agent_service_pb2.MessageType.MESSAGE_TYPE_ERROR,
                    format="text"
                ),
                status=agent_service_pb2.MessageStatus.MESSAGE_STATUS_FAILED
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_service_pb2_grpc.add_AgentCommunicationServiceServicer_to_server(MoneriumService(), server)
    server.add_insecure_port('[::]:50052')
    print("[Monerium gRPC] Server started on port 50052")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve() 