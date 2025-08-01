#!/usr/bin/env python3
"""Protocol Buffer compiler for LLM Agent Bridge."""

import os
import sys
import glob
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
import argparse

import grpc_tools.protoc

from ..config import ProtoConfig
from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ProtoCompiler:
    """Compiles Protocol Buffer files and manages generated code."""
    
    def __init__(self, config: ProtoConfig):
        self.config = config
        self.proto_dir = Path(config.proto_dir)
        self.output_dir = Path(config.output_dir)
        
        # Ensure directories exist
        self.proto_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py in output directory
        init_file = self.output_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Generated Protocol Buffer modules."""\n')
    
    def find_proto_files(self) -> List[Path]:
        """Find all .proto files in the proto directory."""
        proto_files = []
        for pattern in ["*.proto", "**/*.proto"]:
            proto_files.extend(self.proto_dir.glob(pattern))
        return sorted(proto_files)
    
    def check_proto_syntax(self, proto_file: Path) -> bool:
        """Check if a .proto file has valid syntax."""
        try:
            # Use protoc to validate syntax without generating files
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--proto_path={self.proto_dir}",
                "--descriptor_set_out=/dev/null" if os.name != "nt" else "--descriptor_set_out=NUL",
                str(proto_file.relative_to(self.proto_dir))
            ]
            
            # Add include directories
            for include_dir in self.config.include_dirs:
                cmd.append(f"--proto_path={include_dir}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Syntax error in {proto_file}: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check syntax for {proto_file}: {e}")
            return False
    
    def compile_proto_file(self, proto_file: Path) -> bool:
        """Compile a single .proto file."""
        try:
            relative_proto_path = proto_file.relative_to(self.proto_dir)
            logger.info(f"Compiling {relative_proto_path}")
            
            # Build protoc command
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--proto_path={self.proto_dir}",
                f"--python_out={self.output_dir}",
                f"--grpc_python_out={self.output_dir}",
                f"--pyi_out={self.output_dir}",  # Generate type stubs
                str(relative_proto_path)
            ]
            
            # Add include directories
            for include_dir in self.config.include_dirs:
                cmd.append(f"--proto_path={include_dir}")
            
            # Execute compilation
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to compile {proto_file}: {result.stderr}")
                return False
            
            logger.info(f"Successfully compiled {relative_proto_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error compiling {proto_file}: {e}")
            return False
    
    def fix_imports(self) -> None:
        """Fix relative imports in generated files."""
        try:
            # Find all generated _pb2_grpc.py files
            grpc_files = list(self.output_dir.glob("**/*_pb2_grpc.py"))
            
            for grpc_file in grpc_files:
                content = grpc_file.read_text()
                
                # Fix import statements to use relative imports
                lines = content.split('\n')
                fixed_lines = []
                
                for line in lines:
                    if line.strip().startswith('import ') and '_pb2' in line:
                        # Convert absolute imports to relative imports
                        if 'import ' in line and ' as ' in line:
                            parts = line.split(' as ')
                            import_part = parts[0].replace('import ', 'from . import ')
                            line = f"{import_part} as {parts[1]}"
                        elif line.strip().endswith('_pb2'):
                            line = line.replace('import ', 'from . import ')
                    
                    fixed_lines.append(line)
                
                grpc_file.write_text('\n'.join(fixed_lines))
                logger.debug(f"Fixed imports in {grpc_file}")
                
        except Exception as e:
            logger.warning(f"Failed to fix imports: {e}")
    
    def generate_service_registry(self) -> None:
        """Generate a service registry module."""
        try:
            registry_file = self.output_dir / "service_registry.py"
            
            # Find all gRPC service files
            grpc_files = list(self.output_dir.glob("**/*_pb2_grpc.py"))
            
            imports = []
            services = []
            
            for grpc_file in grpc_files:
                module_name = grpc_file.stem  # Remove .py extension
                relative_path = grpc_file.relative_to(self.output_dir)
                module_path = str(relative_path.with_suffix('')).replace(os.sep, '.')
                
                imports.append(f"from . import {module_path}")
                
                # Parse file to find service classes
                content = grpc_file.read_text()
                for line in content.split('\n'):
                    if 'class ' in line and 'Servicer' in line:
                        class_name = line.split('class ')[1].split('(')[0].strip()
                        services.append({
                            'name': class_name,
                            'module': module_path,
                            'file': str(relative_path)
                        })
            
            # Generate registry content
            registry_content = '''"""Auto-generated service registry for gRPC services."""

from typing import Dict, Any, Type
import logging

logger = logging.getLogger(__name__)

# Import all generated modules
'''
            
            for imp in imports:
                registry_content += f"{imp}\n"
            
            registry_content += '''

# Service registry
SERVICES: Dict[str, Dict[str, Any]] = {
'''
            
            for service in services:
                registry_content += f'''    "{service['name']}": {{
        "class": {service['module']}.{service['name']},
        "module": "{service['module']}",
        "file": "{service['file']}"
    }},
'''
            
            registry_content += '''}

def get_service_class(service_name: str) -> Type:
    """Get service class by name."""
    if service_name not in SERVICES:
        raise ValueError(f"Service '{service_name}' not found in registry")
    
    return SERVICES[service_name]["class"]

def list_services() -> Dict[str, Dict[str, Any]]:
    """List all available services."""
    return SERVICES.copy()

def register_service(name: str, service_class: Type, module: str, file: str) -> None:
    """Register a new service."""
    SERVICES[name] = {
        "class": service_class,
        "module": module,
        "file": file
    }
    logger.info(f"Registered service: {name}")
'''
            
            registry_file.write_text(registry_content)
            logger.info(f"Generated service registry: {registry_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate service registry: {e}")
    
    def compile_all(self) -> bool:
        """Compile all .proto files."""
        proto_files = self.find_proto_files()
        
        if not proto_files:
            logger.warning(f"No .proto files found in {self.proto_dir}")
            return True
        
        logger.info(f"Found {len(proto_files)} .proto files to compile")
        
        success_count = 0
        for proto_file in proto_files:
            # Check syntax first
            if not self.check_proto_syntax(proto_file):
                continue
            
            # Compile the file
            if self.compile_proto_file(proto_file):
                success_count += 1
        
        if success_count == len(proto_files):
            logger.info("All .proto files compiled successfully")
            
            # Post-processing
            self.fix_imports()
            self.generate_service_registry()
            
            return True
        else:
            logger.error(f"Failed to compile {len(proto_files) - success_count} out of {len(proto_files)} files")
            return False
    
    def is_compilation_needed(self) -> bool:
        """Check if compilation is needed based on file timestamps."""
        proto_files = self.find_proto_files()
        
        if not proto_files:
            return False
        
        # Check if output directory is empty
        generated_files = list(self.output_dir.glob("**/*_pb2.py"))
        if not generated_files:
            return True
        
        # Check timestamps
        latest_proto_time = max(f.stat().st_mtime for f in proto_files)
        earliest_generated_time = min(f.stat().st_mtime for f in generated_files)
        
        return latest_proto_time > earliest_generated_time
    
    def clean(self) -> None:
        """Clean generated files."""
        try:
            # Remove all generated Python files
            for pattern in ["*_pb2.py", "*_pb2_grpc.py", "*_pb2.pyi", "*_pb2_grpc.pyi"]:
                for file in self.output_dir.glob(f"**/{pattern}"):
                    file.unlink()
                    logger.debug(f"Removed {file}")
            
            # Remove service registry
            registry_file = self.output_dir / "service_registry.py"
            if registry_file.exists():
                registry_file.unlink()
                logger.debug(f"Removed {registry_file}")
            
            logger.info("Cleaned generated files")
            
        except Exception as e:
            logger.error(f"Failed to clean generated files: {e}")


def auto_compile_protos(config: ProtoConfig) -> bool:
    """Auto-compile .proto files if needed."""
    if not config.auto_compile:
        logger.info("Auto-compilation is disabled")
        return True
    
    try:
        compiler = ProtoCompiler(config)
        
        if compiler.is_compilation_needed():
            logger.info("Proto compilation needed, starting compilation...")
            return compiler.compile_all()
        else:
            logger.info("Proto files are up to date")
            return True
            
    except Exception as e:
        logger.error(f"Failed to auto-compile protos: {e}")
        return False


def main():
    """Command-line interface for proto compiler."""
    parser = argparse.ArgumentParser(description="Compile Protocol Buffer files")
    parser.add_argument("--proto-dir", default="protos", help="Directory containing .proto files")
    parser.add_argument("--output-dir", default="generated", help="Output directory for compiled files")
    parser.add_argument("--include-dir", action="append", default=[], help="Additional include directories")
    parser.add_argument("--clean", action="store_true", help="Clean generated files")
    parser.add_argument("--force", action="store_true", help="Force compilation even if files are up to date")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Create config
    config = ProtoConfig(
        proto_dir=args.proto_dir,
        output_dir=args.output_dir,
        include_dirs=args.include_dir,
        auto_compile=True
    )
    
    compiler = ProtoCompiler(config)
    
    try:
        if args.clean:
            compiler.clean()
            return 0
        
        if args.force or compiler.is_compilation_needed():
            success = compiler.compile_all()
            return 0 if success else 1
        else:
            logger.info("Proto files are up to date")
            return 0
            
    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 