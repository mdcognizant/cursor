from universal_api_bridge.mcp.layer import MCPLayer
from universal_api_bridge.config import MCPConfig
from universal_api_bridge.mcp.registry import ServiceInstance
import asyncio

async def register_openai_llm_service():
    try:
        config = MCPConfig()
        mcp_layer = MCPLayer(config)
        openai_service = ServiceInstance(
            id="openai-llm-1",
            name="openai-llm",
            host="localhost",
            port=50051,
            protocol="grpc"
        )
        await mcp_layer.register_service(openai_service)
        print("[MCP] Registered OpenAI LLM gRPC service at localhost:50051")
    except Exception as e:
        print(f"[MCP] Registration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(register_openai_llm_service()) 