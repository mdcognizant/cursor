#!/usr/bin/env python3
"""Basic usage example for LLM Agent Bridge."""

import asyncio
import logging
from pathlib import Path

from llm_agent_bridge import AgentBridge, AgentSDK, BridgeConfig, GRPCServiceConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_setup():
    """Example: Basic setup and configuration."""
    print("=== Basic Setup Example ===")
    
    # Create a bridge with default configuration
    bridge = AgentBridge()
    
    # Add a gRPC service
    bridge.add_grpc_service(
        name="chat-agent",
        host="localhost",
        port=50051,
        use_tls=False
    )
    
    # Get service configuration
    service_config = bridge.get_service_config("chat-agent")
    print(f"Chat agent service: {service_config.endpoint}")
    
    print("Bridge configured successfully!")
    return bridge


def example_custom_config():
    """Example: Custom configuration setup."""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom configuration
    config = BridgeConfig()
    
    # Configure server
    config.server.host = "0.0.0.0"
    config.server.port = 8080
    config.server.workers = 2
    
    # Configure security
    config.security.enable_auth = False  # Disable for demo
    config.security.enable_rate_limiting = True
    config.security.rate_limit_per_minute = 100
    
    # Configure Protocol Buffers
    config.proto.proto_dir = "protos"
    config.proto.output_dir = "generated"
    config.proto.auto_compile = True
    
    # Add gRPC services
    config.add_grpc_service(GRPCServiceConfig(
        name="agent-service",
        host="localhost",
        port=50051,
        use_tls=False,
        timeout=30.0
    ))
    
    # Create bridge with custom config
    bridge = AgentBridge(config=config)
    
    print("Custom configuration applied!")
    return bridge


async def example_sdk_usage():
    """Example: Using the Python SDK."""
    print("\n=== SDK Usage Example ===")
    
    # Create SDK client
    sdk = AgentSDK(
        base_url="http://localhost:8000",
        timeout=30.0
    )
    
    try:
        # Check health status
        health = await sdk.aget_health()
        print(f"Bridge health: {health.status}")
        
        # List available schemas
        schemas = await sdk.alist_schemas()
        print(f"Available schemas: {len(schemas.schemas)}")
        
        # List agents
        agents = await sdk.alist_agents()
        print(f"Available agents: {agents.total_count}")
        
        # Example message sending (would fail without real gRPC backend)
        try:
            response = await sdk.asend_message(
                agent_id="demo-agent",
                content="Hello, world!",
                message_type="TEXT"
            )
            print(f"Agent response: {response.response.content}")
        except Exception as e:
            print(f"Expected error (no gRPC backend): {e}")
    
    finally:
        await sdk.aclose()


async def example_streaming():
    """Example: Streaming message responses."""
    print("\n=== Streaming Example ===")
    
    async with AgentSDK(base_url="http://localhost:8000") as sdk:
        try:
            # Stream message responses
            async for chunk in sdk.astream_message(
                agent_id="demo-agent",
                content="Tell me a story",
                message_type="QUERY"
            ):
                print(f"Chunk: {chunk}")
                
        except Exception as e:
            print(f"Expected error (no gRPC backend): {e}")


def example_docker_deployment():
    """Example: Docker deployment commands."""
    print("\n=== Docker Deployment Example ===")
    
    print("1. Build the Docker image:")
    print("   docker build -t llm-agent-bridge .")
    
    print("\n2. Run the container:")
    print("   docker run -p 8000:8000 llm-agent-bridge")
    
    print("\n3. Run with custom configuration:")
    print("   docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml llm-agent-bridge")
    
    print("\n4. Check health:")
    print("   curl http://localhost:8000/health")


def example_configuration_file():
    """Example: Configuration file usage."""
    print("\n=== Configuration File Example ===")
    
    config_yaml = """
# LLM Agent Bridge Configuration
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  log_level: "info"

security:
  enable_auth: false
  enable_rate_limiting: true
  rate_limit_per_minute: 60

grpc_services:
  chat-agent:
    name: "chat-agent"
    host: "localhost"
    port: 50051
    use_tls: false
    timeout: 30.0
  
  task-orchestrator:
    name: "task-orchestrator" 
    host: "localhost"
    port: 50052
    use_tls: false
    timeout: 60.0

proto:
  proto_dir: "protos"
  output_dir: "generated"
  auto_compile: true

monitoring:
  enable_metrics: true
  enable_health_check: true
"""
    
    # Save example config
    config_path = Path("config.yaml")
    with open(config_path, "w") as f:
        f.write(config_yaml)
    
    print(f"Example configuration saved to: {config_path}")
    
    # Load bridge from config file
    bridge = AgentBridge(config_file="config.yaml")
    print("Bridge loaded from configuration file!")
    
    return bridge


async def run_example_server():
    """Example: Running the bridge server."""
    print("\n=== Running Server Example ===")
    
    # Create bridge with sample configuration
    bridge = example_basic_setup()
    
    print("Starting bridge server...")
    print("Server will run on http://localhost:8000")
    print("- Health check: http://localhost:8000/health")
    print("- API docs: http://localhost:8000/docs")
    print("- Schema info: http://localhost:8000/schema/list")
    
    # Note: In a real deployment, you would call bridge.run()
    # For this example, we'll just show how it's done
    print("\nTo run the server, call: bridge.run()")
    print("Press Ctrl+C to stop the server")


async def main():
    """Run all examples."""
    print("LLM Agent Bridge - Usage Examples")
    print("=" * 50)
    
    try:
        # Basic setup
        bridge = example_basic_setup()
        
        # Custom configuration
        custom_bridge = example_custom_config()
        
        # Configuration file
        file_bridge = example_configuration_file()
        
        # SDK usage
        await example_sdk_usage()
        
        # Streaming example
        await example_streaming()
        
        # Docker deployment
        example_docker_deployment()
        
        # Server example
        await run_example_server()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nTo start the actual server:")
        print("1. Configure your gRPC services")
        print("2. Run: python -m llm_agent_bridge.bridge")
        print("3. Or use: bridge.run() in your code")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 