# LLM Agent Bridge

A Python-based API library that exposes a RESTful interface while internally communicating with gRPC microservices using Protocol Buffers. Designed for developers building applications with multiple LLM agents that need to communicate efficiently and securely.

## Features

### REST Compatibility
- Standard HTTP/JSON requests and responses
- OpenAPI/Swagger documentation
- Compatible with all RESTful API clients (Postman, curl, etc.)

### gRPC Backend
- Internal routing to gRPC services
- Protocol Buffers for message definitions
- Support for unary and streaming RPCs
- TLS-secured communication

### Embedded Tooling
- Automatic .proto file compilation at build/startup
- Embedded Protobuf schema validation and versioning
- Sample agent communication service definitions

### Security & Guardrails
- TLS for gRPC communication
- Authentication and authorization middleware
- Schema validation and input sanitization
- Request rate limiting and monitoring

### Performance & Flexibility
- Async processing and streaming support
- Dynamic routing and payload transformation
- Low-latency agent-to-agent communication
- WebSocket endpoints for real-time updates

### Developer Experience
- Simple Python SDK for calling REST endpoints
- Docker-ready deployment
- CI/CD configuration templates
- Comprehensive documentation and examples

## Quick Start

### Installation

```bash
pip install llm-agent-bridge
```

### Basic Usage

```python
from llm_agent_bridge import AgentBridge, AgentSDK

# Start the bridge server
bridge = AgentBridge()
bridge.run(host="0.0.0.0", port=8000)

# Use the SDK to communicate with agents
sdk = AgentSDK(base_url="http://localhost:8000")
response = sdk.send_message("agent-1", {"text": "Hello, world!"})
```

### Docker Deployment

```bash
docker build -t llm-agent-bridge .
docker run -p 8000:8000 llm-agent-bridge
```

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

## Documentation

- [API Documentation](docs/api.md)
- [gRPC Services](docs/grpc.md)
- [Configuration Guide](docs/configuration.md)
- [Examples](examples/)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development setup and contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details. 