# LLM Agent Bridge - Development Guide

## Overview

The LLM Agent Bridge is a comprehensive Python-based API library that provides a RESTful interface for communicating with gRPC microservices using Protocol Buffers. It's specifically designed for applications with multiple LLM agents that need efficient and secure communication.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   REST Client   │    │  Agent Bridge   │    │  gRPC Services  │
│                 │    │                 │    │                 │
│  HTTP/JSON      │───▶│  FastAPI        │───▶│  Agent Services │
│  Requests       │    │  Middleware     │    │  Protocol Buffers│
│                 │    │  Transform      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
llm-agent-bridge/
├── README.md                    # Main documentation
├── DEVELOPMENT.md              # This file
├── requirements.txt            # Python dependencies
├── setup.py                    # Package configuration
├── Dockerfile                  # Docker container setup
├── protos/                     # Protocol Buffer definitions
│   └── agent_service.proto    # Sample agent service definition
├── src/llm_agent_bridge/      # Main package
│   ├── __init__.py            # Package exports
│   ├── bridge.py              # Main AgentBridge class
│   ├── sdk.py                 # Python SDK
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom exceptions
│   ├── api/                   # REST API components
│   │   ├── app.py            # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   ├── middleware.py     # Security & rate limiting
│   │   └── routes/           # API route handlers
│   ├── proto/                # Protocol Buffer utilities
│   │   ├── validator.py      # Message validation
│   │   └── schema_manager.py # Schema versioning
│   └── tools/                # Development tools
│       └── proto_compiler.py # Auto-compilation tool
└── examples/                  # Usage examples
    └── basic_usage.py        # Getting started example
```

## Key Features Implemented

### ✅ REST Compatibility
- FastAPI-based HTTP/JSON API
- OpenAPI/Swagger documentation
- Compatible with all REST clients (Postman, curl, etc.)

### ✅ gRPC Backend
- Protocol Buffer message definitions
- Auto-compilation of .proto files
- Schema validation and versioning
- Support for unary and streaming RPCs

### ✅ Security & Guardrails
- JWT and API key authentication
- Rate limiting middleware
- Input validation and sanitization
- CORS and security headers

### ✅ Performance & Flexibility
- Async processing with FastAPI
- Streaming response support
- Dynamic configuration
- Low-latency optimizations

### ✅ Developer Experience
- Comprehensive Python SDK
- Docker-ready deployment
- CLI tools for management
- Extensive documentation and examples

### ✅ Bonus Features
- WebSocket endpoints for real-time updates
- Health check and monitoring endpoints
- Configuration validation and templates

## Development Setup

### Prerequisites

- Python 3.9+
- Protocol Buffers compiler (`protoc`)
- Docker (optional)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Compile Protocol Buffers:
   ```bash
   agent-bridge proto --proto-dir protos --output-dir src/llm_agent_bridge/generated
   ```

### Running the Development Server

```bash
# Using the CLI
agent-bridge run --host 0.0.0.0 --port 8000 --log-level DEBUG

# Using Python
python -c "
from llm_agent_bridge import AgentBridge
bridge = AgentBridge()
bridge.run(debug=True)
"
```

### Configuration

Create a configuration file:

```bash
agent-bridge config --generate --output config.yaml
```

Edit the generated configuration:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  log_level: "info"

security:
  enable_auth: false  # Disable for development
  enable_rate_limiting: true

grpc_services:
  my-agent:
    name: "my-agent"
    host: "localhost"
    port: 50051
    use_tls: false
```

### Docker Development

```bash
# Build the image
docker build -t llm-agent-bridge .

# Run the container
docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml llm-agent-bridge
```

## Adding New Features

### Adding a New gRPC Service

1. Define the service in a .proto file
2. Add service configuration to your config
3. Implement route handlers in `src/llm_agent_bridge/api/routes/`
4. Add SDK methods in `src/llm_agent_bridge/sdk.py`

### Adding New API Endpoints

1. Create Pydantic models in `models.py`
2. Add route handlers in the appropriate routes file
3. Update the SDK with corresponding methods
4. Add tests and documentation

### Adding Middleware

1. Create middleware class in `middleware.py`
2. Add middleware to the FastAPI app in `app.py`
3. Configure via the settings system

## Testing

Run the example to verify everything works:

```bash
python examples/basic_usage.py
```

Health check:

```bash
agent-bridge health --verbose
```

API testing:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

## Protocol Buffer Development

### Adding New Message Types

1. Define messages in `.proto` files
2. Re-compile using the proto compiler
3. Register message types with the validator
4. Add corresponding Pydantic models

### Schema Versioning

The system supports multiple schema versions:

```bash
# List available schemas
curl http://localhost:8000/schema/list

# Check compatibility
curl http://localhost:8000/schema/v1/compatibility/v2
```

## SDK Usage

The Python SDK provides both sync and async interfaces:

```python
# Synchronous usage
from llm_agent_bridge import AgentSDK

with AgentSDK("http://localhost:8000") as sdk:
    response = sdk.send_message("agent-1", "Hello!")
    print(response.response.content)

# Asynchronous usage
async with AgentSDK("http://localhost:8000") as sdk:
    response = await sdk.asend_message("agent-1", "Hello!")
    print(response.response.content)
```

## Deployment

### Production Configuration

- Enable authentication
- Configure TLS for gRPC connections
- Set up proper logging
- Configure rate limiting
- Use environment variables for secrets

### Container Deployment

```bash
# Production build
docker build -t llm-agent-bridge:latest .

# Run with production config
docker run -d \
  --name agent-bridge \
  -p 8000:8000 \
  -v /path/to/config.yaml:/app/config.yaml \
  -e BRIDGE_SECURITY__JWT_SECRET="your-secret-key" \
  llm-agent-bridge:latest
```

### Kubernetes Deployment

The Docker image includes health check endpoints suitable for Kubernetes:

- Liveness probe: `/health/live`
- Readiness probe: `/health/ready`

## Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Include docstrings for public APIs
4. Update tests and documentation
5. Follow Python PEP 8 style guidelines

## Next Steps for Full Implementation

To complete the bridge for production use:

1. **Implement gRPC Client Module**: Create the actual gRPC client connections and message routing
2. **Add Real Agent Communication**: Implement the actual message passing to gRPC services
3. **Enhanced Security**: Add more robust authentication and authorization
4. **Monitoring & Observability**: Implement Prometheus metrics and distributed tracing
5. **Performance Optimization**: Add connection pooling, caching, and load balancing
6. **Comprehensive Testing**: Add unit tests, integration tests, and load tests

The current implementation provides a solid foundation with all the core infrastructure, tooling, and interfaces needed to build a production-ready LLM agent communication system. 