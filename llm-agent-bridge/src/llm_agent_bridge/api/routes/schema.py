"""Schema management route handlers."""

from typing import List
from fastapi import APIRouter, Request, HTTPException

from ..models import SchemaListResponse, SchemaInfo

router = APIRouter()


@router.get("/list", response_model=SchemaListResponse, summary="List Schema Versions")
async def list_schemas(request: Request) -> SchemaListResponse:
    """List all available Protocol Buffer schema versions."""
    try:
        schema_manager = getattr(request.app.state, 'schema_manager', None)
        
        if not schema_manager:
            return SchemaListResponse(
                schemas=[],
                current_version=None
            )
        
        versions = schema_manager.list_versions()
        current_version = schema_manager.get_current_version()
        
        schemas = []
        for version in versions:
            version_info = schema_manager.get_version_info(version)
            if version_info:
                schemas.append(SchemaInfo(
                    version=version_info.version,
                    services=version_info.services,
                    file_hash=version_info.file_hash,
                    is_current=(version == current_version)
                ))
        
        return SchemaListResponse(
            schemas=schemas,
            current_version=current_version
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schemas: {str(e)}")


@router.get("/current", summary="Get Current Schema Version")
async def get_current_schema(request: Request) -> dict:
    """Get information about the current active schema version."""
    try:
        schema_manager = getattr(request.app.state, 'schema_manager', None)
        
        if not schema_manager:
            raise HTTPException(status_code=503, detail="Schema manager not available")
        
        current_version = schema_manager.get_current_version()
        
        if not current_version:
            raise HTTPException(status_code=404, detail="No current schema version set")
        
        version_info = schema_manager.get_version_info(current_version)
        
        if not version_info:
            raise HTTPException(status_code=404, detail="Current schema version not found")
        
        return {
            "version": version_info.version,
            "services": version_info.services,
            "file_hash": version_info.file_hash,
            "is_current": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current schema: {str(e)}")


@router.get("/{version}", summary="Get Schema Version Details")
async def get_schema_version(version: str, request: Request) -> dict:
    """Get detailed information about a specific schema version."""
    try:
        schema_manager = getattr(request.app.state, 'schema_manager', None)
        
        if not schema_manager:
            raise HTTPException(status_code=503, detail="Schema manager not available")
        
        version_info = schema_manager.get_version_info(version)
        
        if not version_info:
            raise HTTPException(status_code=404, detail=f"Schema version '{version}' not found")
        
        current_version = schema_manager.get_current_version()
        
        return {
            "version": version_info.version,
            "services": version_info.services,
            "file_hash": version_info.file_hash,
            "is_current": (version == current_version)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema version: {str(e)}")


@router.get("/{old_version}/compatibility/{new_version}", summary="Check Schema Compatibility")
async def check_compatibility(old_version: str, new_version: str, request: Request) -> dict:
    """Check compatibility between two schema versions."""
    try:
        schema_manager = getattr(request.app.state, 'schema_manager', None)
        
        if not schema_manager:
            raise HTTPException(status_code=503, detail="Schema manager not available")
        
        # Check if both versions exist
        old_info = schema_manager.get_version_info(old_version)
        new_info = schema_manager.get_version_info(new_version)
        
        if not old_info:
            raise HTTPException(status_code=404, detail=f"Schema version '{old_version}' not found")
        
        if not new_info:
            raise HTTPException(status_code=404, detail=f"Schema version '{new_version}' not found")
        
        # Check compatibility
        compatibility = schema_manager.check_compatibility(old_version, new_version)
        is_backwards_compatible = schema_manager.is_backwards_compatible(old_version, new_version)
        migration_info = schema_manager.get_migration_info(old_version, new_version)
        
        return {
            "old_version": old_version,
            "new_version": new_version,
            "backwards_compatible": is_backwards_compatible,
            "compatibility": compatibility,
            "migration_info": migration_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check compatibility: {str(e)}") 