"""Schema translator for converting between REST and gRPC formats."""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

from .exceptions import SchemaTranslationError

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Data types for schema translation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


@dataclass
class FieldSchema:
    """Schema definition for a field."""
    name: str
    data_type: DataType
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None
    nested_schema: Optional[Dict[str, 'FieldSchema']] = None


class SchemaTranslator:
    """Translates schemas between REST and gRPC formats."""
    
    def __init__(self):
        self.rest_to_grpc_mappings = self._initialize_mappings()
        
    def _initialize_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default REST-to-gRPC field mappings."""
        return {
            "user_service": {
                "endpoints": {
                    "/api/users": {
                        "GET": "ListUsers",
                        "POST": "CreateUser"
                    },
                    "/api/users/{id}": {
                        "GET": "GetUser",
                        "PUT": "UpdateUser", 
                        "DELETE": "DeleteUser"
                    }
                },
                "schema_mappings": {
                    "user_id": "id",
                    "user_email": "email",
                    "user_name": "name",
                    "created_at": "created_timestamp",
                    "updated_at": "updated_timestamp"
                }
            },
            "order_service": {
                "endpoints": {
                    "/api/orders": {
                        "GET": "ListOrders",
                        "POST": "CreateOrder"
                    },
                    "/api/orders/{id}": {
                        "GET": "GetOrder",
                        "PUT": "UpdateOrder",
                        "DELETE": "CancelOrder"
                    }
                },
                "schema_mappings": {
                    "order_id": "id",
                    "customer_id": "customer.id",
                    "order_total": "total_amount",
                    "order_status": "status",
                    "order_items": "items"
                }
            },
            "payment_service": {
                "endpoints": {
                    "/api/payments": {
                        "POST": "ProcessPayment"
                    },
                    "/api/payments/batch": {
                        "POST": "ProcessBatchPayments"
                    }
                },
                "schema_mappings": {
                    "payment_amount": "amount",
                    "payment_method": "method",
                    "card_number": "card.number",
                    "card_cvv": "card.cvv"
                }
            },
            "analytics_service": {
                "endpoints": {
                    "/api/analytics/realtime": {
                        "POST": "StreamAnalytics"
                    },
                    "/api/analytics/reports": {
                        "GET": "GenerateReport"
                    }
                },
                "schema_mappings": {
                    "metric_name": "metrics",
                    "time_range": "time_window",
                    "filters": "query_filters"
                }
            }
        }
        
    async def translate_rest_to_grpc_request(
        self, 
        service_name: str,
        rest_data: Dict[str, Any], 
        endpoint_path: str = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Translate REST request to gRPC format."""
        
        try:
            # Get service mappings
            service_mappings = self.rest_to_grpc_mappings.get(service_name, {})
            schema_mappings = service_mappings.get("schema_mappings", {})
            
            # Determine gRPC method
            grpc_method = self._determine_grpc_method(service_name, endpoint_path, method)
            
            # Translate request structure
            grpc_request = {
                "method": grpc_method,
                "request": self._translate_fields(rest_data, schema_mappings),
                "metadata": {
                    "source": "rest_api",
                    "translation_version": "1.0",
                    "original_endpoint": endpoint_path,
                    "original_method": method
                }
            }
            
            # Add service-specific transformations
            grpc_request = await self._apply_service_transformations(
                service_name, grpc_request, rest_data
            )
            
            logger.debug(f"Translated REST to gRPC for {service_name}: {grpc_method}")
            return grpc_request
            
        except Exception as e:
            raise SchemaTranslationError(f"Failed to translate REST to gRPC: {e}")
            
    async def translate_grpc_to_rest_response(
        self,
        service_name: str,
        grpc_response: Any,
        original_request: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Translate gRPC response to REST format."""
        
        try:
            # Get reverse mappings
            service_mappings = self.rest_to_grpc_mappings.get(service_name, {})
            schema_mappings = service_mappings.get("schema_mappings", {})
            reverse_mappings = {v: k for k, v in schema_mappings.items()}
            
            # Handle different response types
            if isinstance(grpc_response, dict):
                rest_response = self._translate_fields(grpc_response, reverse_mappings)
            elif isinstance(grpc_response, list):
                rest_response = [
                    self._translate_fields(item, reverse_mappings) 
                    for item in grpc_response
                ]
            else:
                rest_response = {"data": grpc_response}
                
            # Apply service-specific response transformations
            rest_response = await self._apply_response_transformations(
                service_name, rest_response, grpc_response
            )
            
            logger.debug(f"Translated gRPC to REST response for {service_name}")
            return rest_response
            
        except Exception as e:
            raise SchemaTranslationError(f"Failed to translate gRPC to REST: {e}")
            
    def _determine_grpc_method(self, service_name: str, endpoint_path: str, method: str) -> str:
        """Determine gRPC method from REST endpoint."""
        
        service_mappings = self.rest_to_grpc_mappings.get(service_name, {})
        endpoints = service_mappings.get("endpoints", {})
        
        # Try exact match first
        if endpoint_path in endpoints:
            endpoint_methods = endpoints[endpoint_path]
            if method in endpoint_methods:
                return endpoint_methods[method]
                
        # Try pattern matching for parameterized endpoints
        for pattern, methods in endpoints.items():
            if self._match_endpoint_pattern(endpoint_path, pattern):
                if method in methods:
                    return methods[method]
                    
        # Fallback to generic method names
        method_fallbacks = {
            "GET": "Get",
            "POST": "Create",
            "PUT": "Update",
            "DELETE": "Delete",
            "PATCH": "Update"
        }
        
        return method_fallbacks.get(method, "Process")
        
    def _match_endpoint_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern."""
        
        # Simple pattern matching for {id} style parameters
        if "{" not in pattern:
            return path == pattern
            
        path_parts = path.strip("/").split("/")
        pattern_parts = pattern.strip("/").split("/")
        
        if len(path_parts) != len(pattern_parts):
            return False
            
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                # This is a parameter, any value matches
                continue
            elif path_part != pattern_part:
                return False
                
        return True
        
    def _translate_fields(self, data: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Translate field names using mappings."""
        
        if not isinstance(data, dict):
            return data
            
        translated = {}
        
        for key, value in data.items():
            # Check if we have a mapping for this field
            mapped_key = mappings.get(key, key)
            
            # Handle nested mappings (e.g., "customer.id")
            if "." in mapped_key:
                self._set_nested_value(translated, mapped_key, value)
            else:
                # Handle nested objects recursively
                if isinstance(value, dict):
                    translated[mapped_key] = self._translate_fields(value, mappings)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    translated[mapped_key] = [
                        self._translate_fields(item, mappings) for item in value
                    ]
                else:
                    translated[mapped_key] = value
                    
        return translated
        
    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested value using dot notation path."""
        
        parts = path.split(".")
        current = obj
        
        # Navigate/create nested structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Set the final value
        current[parts[-1]] = value
        
    async def _apply_service_transformations(
        self,
        service_name: str,
        grpc_request: Dict[str, Any],
        original_rest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply service-specific transformations."""
        
        if service_name == "user_service":
            # User service specific transformations
            if "password" in grpc_request.get("request", {}):
                # Don't log passwords
                grpc_request["metadata"]["has_sensitive_data"] = True
                
        elif service_name == "order_service":
            # Order service specific transformations
            request_data = grpc_request.get("request", {})
            if "items" in request_data:
                # Calculate total if not provided
                if "total_amount" not in request_data:
                    total = sum(
                        item.get("price", 0) * item.get("quantity", 1)
                        for item in request_data["items"]
                    )
                    request_data["total_amount"] = total
                    
        elif service_name == "payment_service":
            # Payment service specific transformations
            request_data = grpc_request.get("request", {})
            if "card" in request_data:
                # Mask sensitive card data for logging
                grpc_request["metadata"]["has_pci_data"] = True
                
        elif service_name == "analytics_service":
            # Analytics service specific transformations
            request_data = grpc_request.get("request", {})
            if "time_window" in request_data:
                # Ensure time window is properly formatted
                time_window = request_data["time_window"]
                if isinstance(time_window, dict) and "start" in time_window:
                    # Convert to proper timestamp format if needed
                    pass
                    
        return grpc_request
        
    async def _apply_response_transformations(
        self,
        service_name: str,
        rest_response: Any,
        original_grpc: Any
    ) -> Any:
        """Apply service-specific response transformations."""
        
        if service_name == "user_service":
            # Remove sensitive fields from user responses
            if isinstance(rest_response, dict) and "password" in rest_response:
                del rest_response["password"]
            elif isinstance(rest_response, list):
                for user in rest_response:
                    if isinstance(user, dict) and "password" in user:
                        del user["password"]
                        
        elif service_name == "order_service":
            # Add computed fields to order responses
            if isinstance(rest_response, dict) and "items" in rest_response:
                rest_response["item_count"] = len(rest_response["items"])
                
        elif service_name == "payment_service":
            # Mask sensitive payment data
            if isinstance(rest_response, dict) and "card" in rest_response:
                card = rest_response["card"]
                if "number" in card:
                    card["number"] = "**** **** **** " + card["number"][-4:]
                    
        return rest_response
        
    async def validate_schema(self, data: Dict[str, Any], service_name: str) -> bool:
        """Validate data against service schema."""
        
        try:
            # Basic validation - ensure required fields exist
            if service_name == "user_service":
                required_fields = ["email"]
                for field in required_fields:
                    if field not in data:
                        raise SchemaTranslationError(f"Missing required field: {field}")
                        
            elif service_name == "order_service":
                required_fields = ["customer_id", "items"]
                for field in required_fields:
                    if field not in data:
                        raise SchemaTranslationError(f"Missing required field: {field}")
                        
            elif service_name == "payment_service":
                required_fields = ["amount", "method"]
                for field in required_fields:
                    if field not in data:
                        raise SchemaTranslationError(f"Missing required field: {field}")
                        
            return True
            
        except Exception as e:
            logger.error(f"Schema validation failed for {service_name}: {e}")
            return False
            
    def get_service_schema(self, service_name: str) -> Dict[str, Any]:
        """Get schema definition for a service."""
        
        return self.rest_to_grpc_mappings.get(service_name, {})
        
    def add_service_mapping(self, service_name: str, mapping: Dict[str, Any]) -> None:
        """Add new service mapping."""
        
        self.rest_to_grpc_mappings[service_name] = mapping
        logger.info(f"Added service mapping for {service_name}")
        
    def get_supported_services(self) -> List[str]:
        """Get list of supported services."""
        
        return list(self.rest_to_grpc_mappings.keys()) 