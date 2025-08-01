import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import deque
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MoneriumRequest(BaseModel):
    message: str
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class MoneriumResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    mcp_route: str
    service: str
    execution_time: str

class MoneriumMCPGateway:
    def __init__(self):
        # Monerium Configuration with provided credentials
        self.client_id = "54be063f-6cca-11f0-a3e6-4eb54501c717"
        self.client_secret = "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"
        self.auth_code_client = "54bc5fda-6cca-11f0-a3e6-4eb54501c717"
        self.api_base_url = "https://api.monerium.app"  # Production
        # self.api_base_url = "https://api.monerium.dev"  # Sandbox
        
        # MCP Service Registry
        self.service_registry = {
            'monerium-auth': {
                'name': 'Monerium Authentication Service',
                'status': 'healthy',
                'endpoint': '/auth/token',
                'method': 'POST',
                'protocol': 'REST+gRPC',
                'description': 'OAuth2 client credentials authentication'
            },
            'monerium-profile': {
                'name': 'Monerium Profile Service',
                'status': 'healthy',
                'endpoint': '/auth/context',
                'method': 'GET',
                'protocol': 'REST+gRPC',
                'description': 'User profile and context retrieval'
            },
            'monerium-ibans': {
                'name': 'Monerium IBAN Service',
                'status': 'healthy',
                'endpoint': '/ibans',
                'method': 'GET',
                'protocol': 'REST+gRPC',
                'description': 'IBAN management and listing'
            },
            'monerium-balances': {
                'name': 'Monerium Balance Service',
                'status': 'healthy',
                'endpoint': '/balances',
                'method': 'GET',
                'protocol': 'REST+gRPC',
                'description': 'Token balance checking'
            },
            'monerium-wallets': {
                'name': 'Monerium Wallet Service',
                'status': 'healthy',
                'endpoint': '/wallets',
                'method': 'POST',
                'protocol': 'REST+gRPC',
                'description': 'Wallet linking and management'
            },
            'monerium-orders': {
                'name': 'Monerium Order Service',
                'status': 'healthy',
                'endpoint': '/orders',
                'method': 'POST',
                'protocol': 'REST+gRPC',
                'description': 'Order placement and management'
            }
        }
        
        # Circuit Breaker Configuration
        self.circuit_breaker = {
            'failures': 0,
            'threshold': 3,
            'timeout': 30000,
            'state': 'closed'  # closed, open, half-open
        }
        
        # HTTP Client with SSL bypass for corporate networks
        self.http_client = httpx.AsyncClient(
            verify=False,  # Bypass SSL for corporate firewalls
            timeout=httpx.Timeout(30.0)
        )
        
        # Cache for access token
        self.access_token = None
        self.profile_id = None
        
        logger.info("🚀 Monerium MCP Gateway initialized")
        logger.info(f"🏦 API Base URL: {self.api_base_url}")
        logger.info(f"🔑 Client ID: {self.client_id[:8]}...")

    async def route_monerium_request(self, service_name: str, endpoint: str, method: str = "GET", data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """Route requests through MCP service discovery"""
        service = self.service_registry.get(service_name)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found in MCP registry")

        # Circuit breaker check
        if self.circuit_breaker['state'] == 'open':
            raise HTTPException(status_code=503, detail="Circuit breaker open - service temporarily unavailable")

        url = f"{self.api_base_url}{endpoint}"
        
        # Default headers
        default_headers = {
            'User-Agent': 'Monerium-MCP-Gateway/1.0',
            'Content-Type': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)
            
        # Add auth token if available
        if self.access_token and 'Authorization' not in default_headers:
            default_headers['Authorization'] = f'Bearer {self.access_token}'

        try:
            logger.info(f"🔧 MCP Route: {service_name} → {method} {endpoint}")
            
            if method == "POST":
                if service_name == 'monerium-auth':
                    # Special handling for auth endpoint (form data)
                    response = await self.http_client.post(url, data=data, headers=default_headers)
                else:
                    response = await self.http_client.post(url, json=data, headers=default_headers)
            elif method == "GET":
                response = await self.http_client.get(url, headers=default_headers)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not supported")

            response.raise_for_status()
            
            # Reset circuit breaker on success
            self.circuit_breaker['failures'] = 0
            service['status'] = 'healthy'
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = await e.response.atext() if hasattr(e.response, 'atext') else str(e)
            logger.error(f"❌ HTTP {e.response.status_code}: {error_detail}")
            
            # Update circuit breaker
            self.circuit_breaker['failures'] += 1
            if self.circuit_breaker['failures'] >= self.circuit_breaker['threshold']:
                self.circuit_breaker['state'] = 'open'
                asyncio.create_task(self._reset_circuit_breaker())
            
            service['status'] = 'unhealthy'
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
            
        except Exception as e:
            logger.error(f"❌ Request failed: {str(e)}")
            self.circuit_breaker['failures'] += 1
            service['status'] = 'unhealthy'
            raise HTTPException(status_code=500, detail=str(e))

    async def _reset_circuit_breaker(self):
        """Reset circuit breaker after timeout"""
        await asyncio.sleep(self.circuit_breaker['timeout'] / 1000)
        self.circuit_breaker['state'] = 'half-open'
        logger.info("🔄 Circuit breaker reset to half-open")

    # === MONERIUM API METHODS ===
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate using OAuth2 client credentials"""
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        result = await self.route_monerium_request(
            'monerium-auth', 
            '/auth/token', 
            'POST', 
            data=auth_data, 
            headers=headers
        )
        
        self.access_token = result.get('access_token')
        logger.info(f"✅ Authentication successful - Token: {self.access_token[:20]}...")
        
        return result

    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile and context"""
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        result = await self.route_monerium_request('monerium-profile', '/auth/context', 'GET')
        
        if result.get('profiles'):
            self.profile_id = result['profiles'][0]
            logger.info(f"✅ Profile retrieved - ID: {self.profile_id}")
        
        return result

    async def get_ibans(self) -> Dict[str, Any]:
        """Get all IBANs linked to account"""
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        return await self.route_monerium_request('monerium-ibans', '/ibans', 'GET')

    async def get_balance(self, wallet_address: str, chain: str = 'ethereum') -> Dict[str, Any]:
        """Get balance for a specific wallet"""
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        endpoint = f'/balances/{chain}/{wallet_address}'
        return await self.route_monerium_request('monerium-balances', endpoint, 'GET')

    async def link_wallet(self, wallet_address: str, network: str = 'sepolia') -> Dict[str, Any]:
        """Link a new wallet to the profile"""
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        if not self.profile_id:
            raise HTTPException(status_code=400, detail="Profile ID required - get profile first")

        wallet_data = {
            'address': wallet_address,
            'chain': 'ethereum',
            'network': network,
            'profiles': [self.profile_id]
        }
        
        return await self.route_monerium_request('monerium-wallets', '/wallets', 'POST', data=wallet_data)

    async def place_order(self, wallet_address: str, amount: str, currency: str, recipient_iban: str, recipient_name: str) -> Dict[str, Any]:
        """Place a money transfer order"""
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Authentication required")

        order_data = {
            'address': wallet_address,
            'amount': amount,
            'currency': currency,
            'counterpart': {
                'identifier': {
                    'standard': 'iban',
                    'iban': recipient_iban
                },
                'details': {
                    'name': recipient_name
                }
            },
            'message': f"Transfer via MCP Gateway at {datetime.now().isoformat()}"
        }
        
        return await self.route_monerium_request('monerium-orders', '/orders', 'POST', data=order_data)

class LiveMonitorEvent(BaseModel):
    timestamp: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    user_action: Optional[str] = None
    status: Optional[str] = None

class ClaudeChatMessage(BaseModel):
    id: str
    message: str
    timestamp: str
    user_id: str
    session_id: str
    status: str = "pending"  # pending, answered, error
    claude_response: Optional[str] = None
    response_timestamp: Optional[str] = None

class ClaudeChatService:
    def __init__(self):
        self.pending_messages = {}  # message_id -> ClaudeChatMessage
        self.conversation_history = deque(maxlen=100)  # Keep last 100 exchanges
        
    def add_user_message(self, message: str, session_id: str) -> str:
        """Add a user message and return message ID"""
        import uuid
        message_id = f"claude_msg_{int(datetime.now().timestamp() * 1000)}"
        
        chat_message = ClaudeChatMessage(
            id=message_id,
            message=message,
            timestamp=datetime.now().isoformat(),
            user_id="user",
            session_id=session_id,
            status="pending"
        )
        
        self.pending_messages[message_id] = chat_message
        print(f"[CLAUDE CHAT] 💬 User: {message}")
        print(f"[CLAUDE CHAT] 🔄 Message ID: {message_id} - Waiting for Claude response...")
        
        return message_id
    
    def add_claude_response(self, message_id: str, response: str) -> bool:
        """Add Claude's response to a pending message"""
        if message_id in self.pending_messages:
            self.pending_messages[message_id].claude_response = response
            self.pending_messages[message_id].status = "answered"
            self.pending_messages[message_id].response_timestamp = datetime.now().isoformat()
            
            # Move to conversation history
            self.conversation_history.append(self.pending_messages[message_id])
            
            print(f"[CLAUDE CHAT] 🤖 Claude responded to {message_id}")
            return True
        return False
    
    def get_pending_message(self, message_id: str) -> Optional[ClaudeChatMessage]:
        """Get a pending message"""
        return self.pending_messages.get(message_id)
    
    def get_recent_conversation(self, limit: int = 10):
        """Get recent conversation history"""
        return list(self.conversation_history)[-limit:]

class LiveMonitoringService:
    def __init__(self):
        self.events = deque(maxlen=1000)  # Keep last 1000 events
        self.active_session = None
        self.session_start = datetime.now()
        
    def add_event(self, event: LiveMonitorEvent):
        """Add a new monitoring event"""
        self.events.append({
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'message': event.message,
            'data': event.data,
            'user_action': event.user_action,
            'status': event.status
        })
        
        # Log to console for real-time monitoring
        print(f"[LIVE MONITOR] {event.timestamp} - {event.event_type}: {event.message}")
        if event.data:
            print(f"[LIVE DATA] {json.dumps(event.data, indent=2)}")
    
    def get_recent_events(self, limit: int = 50):
        """Get recent events for analysis"""
        return list(self.events)[-limit:]
    
    def get_session_summary(self):
        """Get summary of current session"""
        return {
            'session_start': self.session_start.isoformat(),
            'total_events': len(self.events),
            'recent_events': self.get_recent_events(10),
            'event_types': self._get_event_type_counts()
        }
    
    def _get_event_type_counts(self):
        """Count events by type"""
        counts = {}
        for event in self.events:
            event_type = event['event_type']
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

# Initialize services
live_monitor = LiveMonitoringService()
claude_chat = ClaudeChatService()

# FastAPI Application
app = FastAPI(title="Monerium MCP Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize gateway
gateway = MoneriumMCPGateway()

@app.post("/monerium/authenticate")
async def authenticate():
    """Authenticate with Monerium API"""
    try:
        start_time = datetime.now()
        result = await gateway.authenticate()
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-auth → OAuth2 Token",
            service="monerium-auth",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-auth → Failed",
            service="monerium-auth",
            execution_time="0s"
        )

@app.post("/monerium/profile")
async def get_profile():
    """Get user profile"""
    try:
        start_time = datetime.now()
        result = await gateway.get_profile()
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-profile → Profile Context",
            service="monerium-profile",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-profile → Failed",
            service="monerium-profile",
            execution_time="0s"
        )

@app.get("/monerium/ibans")
async def get_ibans():
    """Get all IBANs"""
    try:
        start_time = datetime.now()
        result = await gateway.get_ibans()
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-ibans → IBAN List",
            service="monerium-ibans",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-ibans → Failed",
            service="monerium-ibans",
            execution_time="0s"
        )

@app.post("/monerium/balance")
async def get_balance(request: MoneriumRequest):
    """Get wallet balance"""
    try:
        wallet_address = request.data.get('wallet_address') if request.data else None
        if not wallet_address:
            raise HTTPException(status_code=400, detail="wallet_address required in data")
            
        start_time = datetime.now()
        result = await gateway.get_balance(wallet_address)
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-balances → Balance Check",
            service="monerium-balances",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-balances → Failed",
            service="monerium-balances",
            execution_time="0s"
        )

@app.post("/monerium/link-wallet")
async def link_wallet(request: MoneriumRequest):
    """Link a new wallet"""
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="Request data required")
            
        wallet_address = request.data.get('wallet_address')
        network = request.data.get('network', 'sepolia')
        
        if not wallet_address:
            raise HTTPException(status_code=400, detail="wallet_address required")
            
        start_time = datetime.now()
        result = await gateway.link_wallet(wallet_address, network)
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-wallets → Wallet Link",
            service="monerium-wallets",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-wallets → Failed",
            service="monerium-wallets",
            execution_time="0s"
        )

@app.post("/monerium/place-order")
async def place_order(request: MoneriumRequest):
    """Place a transfer order"""
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="Request data required")
            
        required_fields = ['wallet_address', 'amount', 'currency', 'recipient_iban', 'recipient_name']
        for field in required_fields:
            if field not in request.data:
                raise HTTPException(status_code=400, detail=f"{field} required")
                
        start_time = datetime.now()
        result = await gateway.place_order(
            request.data['wallet_address'],
            request.data['amount'],
            request.data['currency'],
            request.data['recipient_iban'],
            request.data['recipient_name']
        )
        execution_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"
        
        return MoneriumResponse(
            success=True,
            data=result,
            mcp_route="MCP → monerium-orders → Order Placement",
            service="monerium-orders",
            execution_time=execution_time
        )
    except Exception as e:
        return MoneriumResponse(
            success=False,
            error=str(e),
            mcp_route="MCP → monerium-orders → Failed",
            service="monerium-orders",
            execution_time="0s"
        )

@app.post("/live-monitor/event")
async def receive_live_event(event: LiveMonitorEvent):
    """Receive live monitoring events from HTML interface"""
    try:
        live_monitor.add_event(event)
        return {"status": "received", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Failed to process live event: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/live-monitor/events")
async def get_live_events(limit: int = 50):
    """Get recent live monitoring events"""
    return {
        "events": live_monitor.get_recent_events(limit),
        "total_events": len(live_monitor.events)
    }

@app.get("/live-monitor/session")
async def get_session_summary():
    """Get current monitoring session summary"""
    return live_monitor.get_session_summary()

@app.get("/live-monitor/stream")
async def stream_events():
    """Stream events in real-time (Server-Sent Events)"""
    from fastapi.responses import StreamingResponse
    
    async def event_stream():
        last_count = 0
        while True:
            current_count = len(live_monitor.events)
            if current_count > last_count:
                # New events available
                new_events = live_monitor.get_recent_events(current_count - last_count)
                for event in new_events:
                    yield f"data: {json.dumps(event)}\n\n"
                last_count = current_count
            await asyncio.sleep(1)
    
    return StreamingResponse(event_stream(), media_type="text/plain")

# CLAUDE CHAT ENDPOINTS - REAL AI CONVERSATION
@app.post("/claude-chat/send")
async def send_claude_message(request: dict):
    """Send a message to Claude and wait for response"""
    try:
        user_message = request.get("message", "").strip()
        session_id = request.get("session_id", "default")
        
        if not user_message:
            return {"status": "error", "error": "Message cannot be empty"}
        
        # Add user message to Claude chat service
        message_id = claude_chat.add_user_message(user_message, session_id)
        
        # Log to live monitor
        live_monitor.add_event(LiveMonitorEvent(
            timestamp=datetime.now().isoformat(),
            event_type="claude_chat_request",
            message=f"User message sent to Claude: {user_message}",
            data={"message_id": message_id, "user_message": user_message},
            user_action="claude_chat"
        ))
        
        # Return immediately with message ID (Claude will respond asynchronously)
        return {
            "status": "sent",
            "message_id": message_id,
            "message": "Message sent to Claude. Check /claude-chat/status/{message_id} for response.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/claude-chat/status/{message_id}")
async def get_claude_response_status(message_id: str):
    """Check if Claude has responded to a message"""
    try:
        message = claude_chat.get_pending_message(message_id)
        if not message:
            return {"status": "not_found", "error": "Message ID not found"}
        
        if message.status == "answered":
            return {
                "status": "answered",
                "user_message": message.message,
                "claude_response": message.claude_response,
                "user_timestamp": message.timestamp,
                "response_timestamp": message.response_timestamp,
                "message_id": message_id
            }
        else:
            return {
                "status": "pending",
                "message": "Claude is thinking... Please wait a moment.",
                "message_id": message_id,
                "user_message": message.message,
                "timestamp": message.timestamp
            }
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/claude-chat/respond")
async def claude_respond(request: dict):
    """Endpoint for Claude to provide responses (used by AI assistant)"""
    try:
        message_id = request.get("message_id")
        response = request.get("response")
        
        if not message_id or not response:
            return {"status": "error", "error": "message_id and response required"}
        
        success = claude_chat.add_claude_response(message_id, response)
        
        if success:
            # Log to live monitor
            live_monitor.add_event(LiveMonitorEvent(
                timestamp=datetime.now().isoformat(),
                event_type="claude_chat_response",
                message=f"Claude responded to message {message_id}",
                data={"message_id": message_id, "response_preview": response[:100] + "..."},
                user_action="claude_response"
            ))
            
            return {"status": "success", "message": "Response added successfully"}
        else:
            return {"status": "error", "error": "Message ID not found"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/claude-chat/conversation")
async def get_conversation_history(limit: int = 10):
    """Get recent conversation history with Claude"""
    try:
        history = claude_chat.get_recent_conversation(limit)
        return {
            "status": "success",
            "conversation": [
                {
                    "user_message": msg.message,
                    "claude_response": msg.claude_response,
                    "user_timestamp": msg.timestamp,
                    "response_timestamp": msg.response_timestamp,
                    "message_id": msg.id
                } for msg in history
            ],
            "total_messages": len(history)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/live-monitor/analysis-request")
async def request_analysis(request: dict):
    """Request analysis of current session - this endpoint will be used to signal when user wants analysis"""
    try:
        live_monitor.add_event(LiveMonitorEvent(
            timestamp=datetime.now().isoformat(),
            event_type="analysis_request",
            message="User requested live analysis",
            data=request,
            user_action="request_analysis"
        ))
        
        # Generate analysis summary
        session_summary = live_monitor.get_session_summary()
        recent_events = live_monitor.get_recent_events(20)
        
        analysis = {
            "session_summary": session_summary,
            "recent_events": recent_events,
            "analysis_timestamp": datetime.now().isoformat(),
            "status": "ready_for_ai_analysis"
        }
        
        return analysis
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Monerium MCP Gateway",
        "timestamp": datetime.now().isoformat(),
        "services": gateway.service_registry,
        "circuit_breaker": gateway.circuit_breaker,
        "auth_status": "authenticated" if gateway.access_token else "not_authenticated"
    }

@app.get("/services")
async def list_services():
    """List all registered MCP services"""
    return {
        "mcp_services": gateway.service_registry,
        "circuit_breaker_status": gateway.circuit_breaker,
        "total_services": len(gateway.service_registry)
    }

if __name__ == "__main__":
    print("🚀 Starting Monerium MCP Gateway...")
    print(f"🏦 Monerium API: {gateway.api_base_url}")
    print(f"🔑 Client ID: {gateway.client_id[:8]}...")
    print("🌐 Gateway: http://localhost:8004")
    
    uvicorn.run(app, host="0.0.0.0", port=8004) 