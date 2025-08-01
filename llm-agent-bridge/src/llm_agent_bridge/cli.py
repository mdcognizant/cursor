#!/usr/bin/env python3
"""Command-line interface for LLM Agent Bridge."""

import argparse
import logging
import sys
from pathlib import Path

from .bridge import AgentBridge, create_bridge
from .config import BridgeConfig, GRPCServiceConfig
from .tools.proto_compiler import main as proto_main


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def cmd_run(args) -> None:
    """Run the bridge server."""
    setup_logging(args.log_level)
    
    # Create bridge configuration
    if args.config:
        bridge = AgentBridge(config_file=args.config)
    else:
        # Create with command line overrides
        config_overrides = {}
        if args.host:
            config_overrides['host'] = args.host
        if args.port:
            config_overrides['port'] = args.port
        if args.workers:
            config_overrides['workers'] = args.workers
        
        bridge = create_bridge(**config_overrides)
    
    # Add gRPC services from command line
    if args.grpc_service:
        for service_spec in args.grpc_service:
            try:
                name, endpoint = service_spec.split('=', 1)
                host, port = endpoint.split(':', 1)
                bridge.add_grpc_service(
                    name=name,
                    host=host,
                    port=int(port),
                    use_tls=args.tls
                )
                print(f"Added gRPC service: {name} at {endpoint}")
            except ValueError:
                print(f"Invalid service specification: {service_spec}")
                print("Format: name=host:port")
                sys.exit(1)
    
    # Run the bridge
    print(f"Starting LLM Agent Bridge server...")
    print(f"Server will be available at: http://{bridge.config.server.host}:{bridge.config.server.port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        bridge.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


def cmd_proto(args) -> None:
    """Compile Protocol Buffer files."""
    # Delegate to proto compiler
    original_argv = sys.argv
    sys.argv = ['proto-compile'] + args.proto_args
    try:
        exit_code = proto_main()
        sys.exit(exit_code)
    finally:
        sys.argv = original_argv


def cmd_health(args) -> None:
    """Check bridge health."""
    import httpx
    
    try:
        url = f"http://{args.host}:{args.port}/health"
        response = httpx.get(url, timeout=args.timeout)
        response.raise_for_status()
        
        health_data = response.json()
        status = health_data.get('status', 'unknown')
        
        print(f"Bridge Status: {status.upper()}")
        print(f"Version: {health_data.get('version', 'unknown')}")
        print(f"Uptime: {health_data.get('uptime_seconds', 0)} seconds")
        
        if args.verbose:
            checks = health_data.get('checks', {})
            print("\nComponent Health:")
            for component, check in checks.items():
                status = "✓" if check.get('healthy', False) else "✗"
                message = check.get('message', 'No message')
                print(f"  {status} {component}: {message}")
        
        # Exit with non-zero code if unhealthy
        if status not in ['healthy', 'degraded']:
            sys.exit(1)
            
    except httpx.RequestError as e:
        print(f"Failed to connect to bridge: {e}")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"Bridge returned error: {e.response.status_code}")
        sys.exit(1)


def cmd_config(args) -> None:
    """Generate or validate configuration."""
    if args.generate:
        config_template = """# LLM Agent Bridge Configuration
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  log_level: "info"
  reload: false

security:
  enable_auth: true
  jwt_secret: "your-secret-key-here"
  jwt_algorithm: "HS256"
  jwt_expiry_hours: 24
  enable_rate_limiting: true
  rate_limit_per_minute: 60
  cors_origins: ["*"]

grpc_services:
  example-agent:
    name: "example-agent"
    host: "localhost"
    port: 50051
    use_tls: false
    timeout: 30.0
    max_retries: 3

proto:
  proto_dir: "protos"
  output_dir: "generated"
  auto_compile: true
  include_dirs: []

monitoring:
  enable_metrics: true
  metrics_port: 9090
  enable_health_check: true
  health_check_path: "/health"

environment: "development"
debug: false
"""
        output_file = args.output or "bridge-config.yaml"
        with open(output_file, 'w') as f:
            f.write(config_template)
        print(f"Configuration template generated: {output_file}")
        
    elif args.validate:
        try:
            config = BridgeConfig.load_from_file(args.validate)
            issues = config.validate_config()
            
            if issues:
                print("Configuration validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid!")
        except Exception as e:
            print(f"Failed to validate configuration: {e}")
            sys.exit(1)


def cmd_version(args) -> None:
    """Show version information."""
    from . import __version__
    print(f"LLM Agent Bridge v{__version__}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Agent Bridge - REST to gRPC bridge for LLM agent communication",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the bridge server')
    run_parser.add_argument('--config', '-c', help='Configuration file path')
    run_parser.add_argument('--host', help='Server host (default: 0.0.0.0)')
    run_parser.add_argument('--port', type=int, help='Server port (default: 8000)')
    run_parser.add_argument('--workers', type=int, help='Number of worker processes')
    run_parser.add_argument('--log-level', default='INFO', 
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                          help='Logging level')
    run_parser.add_argument('--grpc-service', action='append',
                          help='Add gRPC service (format: name=host:port)')
    run_parser.add_argument('--tls', action='store_true',
                          help='Use TLS for gRPC connections')
    run_parser.set_defaults(func=cmd_run)
    
    # Proto command
    proto_parser = subparsers.add_parser('proto', help='Compile Protocol Buffer files')
    proto_parser.add_argument('proto_args', nargs='*', help='Arguments for proto compiler')
    proto_parser.set_defaults(func=cmd_proto)
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check bridge health')
    health_parser.add_argument('--host', default='localhost', help='Bridge host')
    health_parser.add_argument('--port', type=int, default=8000, help='Bridge port')
    health_parser.add_argument('--timeout', type=float, default=10.0, help='Request timeout')
    health_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show detailed health information')
    health_parser.set_defaults(func=cmd_health)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--generate', action='store_true',
                            help='Generate configuration template')
    config_group.add_argument('--validate', help='Validate configuration file')
    config_parser.add_argument('--output', '-o', help='Output file for generated config')
    config_parser.set_defaults(func=cmd_config)
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    version_parser.set_defaults(func=cmd_version)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 