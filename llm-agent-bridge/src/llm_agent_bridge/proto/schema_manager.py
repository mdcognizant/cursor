"""Schema manager for Protocol Buffer versioning and compatibility."""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
import hashlib
import json

from google.protobuf.descriptor import FileDescriptor, ServiceDescriptor
from google.protobuf.descriptor_pool import DescriptorPool

from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SchemaVersion:
    """Represents a version of a Protocol Buffer schema."""
    
    def __init__(self, version: str, file_hash: str, services: List[str]):
        self.version = version
        self.file_hash = file_hash
        self.services = services
        self.timestamp = None


class SchemaManager:
    """Manages Protocol Buffer schema versions and compatibility."""
    
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.descriptor_pool = DescriptorPool()
        self._versions: Dict[str, SchemaVersion] = {}
        self._current_version: Optional[str] = None
        self._file_descriptors: Dict[str, FileDescriptor] = {}
        
        # Ensure schema directory exists
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing schemas
        self._load_existing_schemas()
    
    def _load_existing_schemas(self) -> None:
        """Load existing schema versions from disk."""
        version_file = self.schema_dir / "versions.json"
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    data = json.load(f)
                
                for version_data in data.get('versions', []):
                    version = SchemaVersion(
                        version=version_data['version'],
                        file_hash=version_data['file_hash'],
                        services=version_data['services']
                    )
                    self._versions[version.version] = version
                
                self._current_version = data.get('current_version')
                logger.info(f"Loaded {len(self._versions)} schema versions")
                
            except Exception as e:
                logger.error(f"Failed to load schema versions: {e}")
    
    def _save_schemas(self) -> None:
        """Save schema versions to disk."""
        version_file = self.schema_dir / "versions.json"
        
        try:
            data = {
                'current_version': self._current_version,
                'versions': [
                    {
                        'version': v.version,
                        'file_hash': v.file_hash,
                        'services': v.services
                    }
                    for v in self._versions.values()
                ]
            }
            
            with open(version_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save schema versions: {e}")
    
    def _calculate_file_hash(self, proto_files: List[Path]) -> str:
        """Calculate hash of proto files for versioning."""
        content = ""
        for proto_file in sorted(proto_files):
            if proto_file.exists():
                content += proto_file.read_text()
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def register_schema(self, version: str, proto_files: List[Path], 
                       service_descriptors: List[ServiceDescriptor]) -> bool:
        """Register a new schema version."""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(proto_files)
            
            # Extract service names
            services = [desc.full_name for desc in service_descriptors]
            
            # Check if this version already exists
            if version in self._versions:
                existing = self._versions[version]
                if existing.file_hash == file_hash:
                    logger.info(f"Schema version {version} already registered")
                    return True
                else:
                    logger.warning(f"Schema version {version} exists with different hash")
                    return False
            
            # Create new version
            schema_version = SchemaVersion(version, file_hash, services)
            self._versions[version] = schema_version
            
            # Set as current if it's the first version
            if not self._current_version:
                self._current_version = version
            
            # Save to disk
            self._save_schemas()
            
            logger.info(f"Registered schema version {version} with {len(services)} services")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register schema version {version}: {e}")
            return False
    
    def set_current_version(self, version: str) -> bool:
        """Set the current active schema version."""
        if version not in self._versions:
            logger.error(f"Schema version {version} not found")
            return False
        
        self._current_version = version
        self._save_schemas()
        logger.info(f"Set current schema version to {version}")
        return True
    
    def get_current_version(self) -> Optional[str]:
        """Get the current active schema version."""
        return self._current_version
    
    def get_version_info(self, version: str) -> Optional[SchemaVersion]:
        """Get information about a specific schema version."""
        return self._versions.get(version)
    
    def list_versions(self) -> List[str]:
        """List all registered schema versions."""
        return list(self._versions.keys())
    
    def check_compatibility(self, old_version: str, new_version: str) -> Dict[str, List[str]]:
        """Check compatibility between two schema versions."""
        old_schema = self._versions.get(old_version)
        new_schema = self._versions.get(new_version)
        
        if not old_schema or not new_schema:
            raise ConfigurationError(f"Schema version not found")
        
        compatibility = {
            'added_services': [],
            'removed_services': [],
            'common_services': []
        }
        
        old_services = set(old_schema.services)
        new_services = set(new_schema.services)
        
        compatibility['added_services'] = list(new_services - old_services)
        compatibility['removed_services'] = list(old_services - new_services)
        compatibility['common_services'] = list(old_services & new_services)
        
        return compatibility
    
    def is_backwards_compatible(self, old_version: str, new_version: str) -> bool:
        """Check if new version is backwards compatible with old version."""
        try:
            compatibility = self.check_compatibility(old_version, new_version)
            
            # Backwards compatible if no services were removed
            return len(compatibility['removed_services']) == 0
            
        except Exception as e:
            logger.error(f"Failed to check compatibility: {e}")
            return False
    
    def get_migration_info(self, from_version: str, to_version: str) -> Dict[str, any]:
        """Get migration information between versions."""
        compatibility = self.check_compatibility(from_version, to_version)
        
        migration_info = {
            'from_version': from_version,
            'to_version': to_version,
            'backwards_compatible': len(compatibility['removed_services']) == 0,
            'changes': compatibility,
            'migration_steps': []
        }
        
        # Generate migration steps
        if compatibility['removed_services']:
            migration_info['migration_steps'].append({
                'type': 'warning',
                'message': f"Services removed: {', '.join(compatibility['removed_services'])}"
            })
        
        if compatibility['added_services']:
            migration_info['migration_steps'].append({
                'type': 'info',
                'message': f"New services available: {', '.join(compatibility['added_services'])}"
            })
        
        return migration_info
    
    def cleanup_old_versions(self, keep_latest: int = 5) -> None:
        """Clean up old schema versions, keeping only the latest N versions."""
        if len(self._versions) <= keep_latest:
            return
        
        # Sort versions by name (assuming semantic versioning)
        sorted_versions = sorted(self._versions.keys(), reverse=True)
        versions_to_remove = sorted_versions[keep_latest:]
        
        for version in versions_to_remove:
            if version != self._current_version:  # Never remove current version
                del self._versions[version]
                logger.info(f"Removed old schema version: {version}")
        
        self._save_schemas()
    
    def export_schema(self, version: str, output_file: Path) -> bool:
        """Export a schema version to a file."""
        schema_version = self._versions.get(version)
        if not schema_version:
            logger.error(f"Schema version {version} not found")
            return False
        
        try:
            export_data = {
                'version': schema_version.version,
                'file_hash': schema_version.file_hash,
                'services': schema_version.services,
                'exported_at': None  # Would set current timestamp
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported schema version {version} to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export schema version {version}: {e}")
            return False 