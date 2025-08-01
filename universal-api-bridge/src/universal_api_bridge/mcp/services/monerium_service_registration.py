from universal_api_bridge.mcp.layer import MCPLayer
from universal_api_bridge.config import MCPConfig
from universal_api_bridge.mcp.registry import ServiceInstance
import asyncio

async def register_monerium_service():
    try:
        config = MCPConfig()
        mcp_layer = MCPLayer(config)
        monerium_service = ServiceInstance(
            id="monerium-api-1",
            name="monerium-api",
            host="localhost",
            port=50052,
            protocol="grpc"
        )
        await mcp_layer.register_service(monerium_service)
        print("[MCP] Registered Monerium API gRPC service at localhost:50052")
    except Exception as e:
        print(f"[MCP] Monerium registration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(register_monerium_service()) 