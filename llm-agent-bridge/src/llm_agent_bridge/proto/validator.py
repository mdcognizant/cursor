"""Protocol Buffer validation utilities."""

import logging
from typing import Any, Dict, List, Optional, Type, Union
from google.protobuf.message import Message
from google.protobuf.descriptor import ServiceDescriptor, MethodDescriptor
from google.protobuf.json_format import MessageToDict, Parse, ParseError
from google.protobuf.descriptor_pool import DescriptorPool

from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


class ProtoValidator:
    """Validates Protocol Buffer messages and provides schema validation."""
    
    def __init__(self):
        self.descriptor_pool = DescriptorPool()
        self._message_types: Dict[str, Type[Message]] = {}
        self._service_descriptors: Dict[str, ServiceDescriptor] = {}
    
    def register_message_type(self, message_class: Type[Message]) -> None:
        """Register a Protocol Buffer message type."""
        message_name = message_class.DESCRIPTOR.full_name
        self._message_types[message_name] = message_class
        logger.debug(f"Registered message type: {message_name}")
    
    def register_service_descriptor(self, service_descriptor: ServiceDescriptor) -> None:
        """Register a service descriptor."""
        service_name = service_descriptor.full_name
        self._service_descriptors[service_name] = service_descriptor
        logger.debug(f"Registered service: {service_name}")
    
    def get_message_type(self, message_name: str) -> Optional[Type[Message]]:
        """Get a registered message type by name."""
        return self._message_types.get(message_name)
    
    def get_service_descriptor(self, service_name: str) -> Optional[ServiceDescriptor]:
        """Get a registered service descriptor by name."""
        return self._service_descriptors.get(service_name)
    
    def validate_message(self, message: Message, strict: bool = True) -> bool:
        """Validate a Protocol Buffer message."""
        try:
            # Check if message is complete (all required fields are set)
            if strict and not message.IsInitialized():
                missing_fields = []
                for field, value in message.ListFields():
                    if field.label == field.LABEL_REQUIRED and not value:
                        missing_fields.append(field.name)
                
                if missing_fields:
                    raise ValidationError(
                        f"Missing required fields: {', '.join(missing_fields)}",
                        field=missing_fields[0]
                    )
            
            # Custom validation rules
            self._validate_message_custom(message)
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Message validation failed: {str(e)}")
    
    def _validate_message_custom(self, message: Message) -> None:
        """Apply custom validation rules based on message type."""
        message_name = message.DESCRIPTOR.full_name
        
        # Add custom validation rules here
        if "SendMessageRequest" in message_name:
            self._validate_send_message_request(message)
        elif "Agent" in message_name:
            self._validate_agent_message(message)
        elif "Task" in message_name:
            self._validate_task_message(message)
    
    def _validate_send_message_request(self, message: Message) -> None:
        """Validate SendMessageRequest messages."""
        if hasattr(message, 'agent_id') and not message.agent_id.strip():
            raise ValidationError("agent_id cannot be empty", field="agent_id")
        
        if hasattr(message, 'message') and hasattr(message.message, 'content'):
            if not message.message.content.strip():
                raise ValidationError("message content cannot be empty", field="message.content")
    
    def _validate_agent_message(self, message: Message) -> None:
        """Validate Agent messages."""
        if hasattr(message, 'id') and not message.id.strip():
            raise ValidationError("agent id cannot be empty", field="id")
        
        if hasattr(message, 'name') and not message.name.strip():
            raise ValidationError("agent name cannot be empty", field="name")
    
    def _validate_task_message(self, message: Message) -> None:
        """Validate Task messages."""
        if hasattr(message, 'id') and not message.id.strip():
            raise ValidationError("task id cannot be empty", field="id")
        
        if hasattr(message, 'steps'):
            for i, step in enumerate(message.steps):
                if hasattr(step, 'agent_id') and not step.agent_id.strip():
                    raise ValidationError(
                        f"task step {i} agent_id cannot be empty",
                        field=f"steps[{i}].agent_id"
                    )
    
    def json_to_proto(self, json_data: Union[str, Dict[str, Any]], 
                      message_class: Type[Message], 
                      strict: bool = True) -> Message:
        """Convert JSON data to Protocol Buffer message."""
        try:
            message = message_class()
            
            if isinstance(json_data, str):
                Parse(json_data, message)
            else:
                # Convert dict to JSON string then parse
                import json
                json_str = json.dumps(json_data)
                Parse(json_str, message)
            
            # Validate the parsed message
            if strict:
                self.validate_message(message, strict=strict)
            
            return message
            
        except ParseError as e:
            raise ValidationError(f"Failed to parse JSON to protobuf: {str(e)}")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"JSON to protobuf conversion failed: {str(e)}")
    
    def proto_to_json(self, message: Message, 
                      include_default_values: bool = False) -> Dict[str, Any]:
        """Convert Protocol Buffer message to JSON-compatible dict."""
        try:
            return MessageToDict(
                message,
                preserving_proto_field_name=True,
                including_default_value_fields=include_default_values
            )
        except Exception as e:
            raise ValidationError(f"Protobuf to JSON conversion failed: {str(e)}")
    
    def validate_service_method(self, service_name: str, method_name: str) -> MethodDescriptor:
        """Validate that a service method exists and return its descriptor."""
        service_descriptor = self.get_service_descriptor(service_name)
        if not service_descriptor:
            raise ValidationError(f"Service '{service_name}' not found")
        
        method_descriptor = service_descriptor.FindMethodByName(method_name)
        if not method_descriptor:
            raise ValidationError(f"Method '{method_name}' not found in service '{service_name}'")
        
        return method_descriptor
    
    def get_method_signature(self, service_name: str, method_name: str) -> Dict[str, Any]:
        """Get the signature information for a service method."""
        method_descriptor = self.validate_service_method(service_name, method_name)
        
        return {
            "service": service_name,
            "method": method_name,
            "input_type": method_descriptor.input_type.full_name,
            "output_type": method_descriptor.output_type.full_name,
            "client_streaming": method_descriptor.client_streaming,
            "server_streaming": method_descriptor.server_streaming,
        }
    
    def list_services(self) -> List[Dict[str, Any]]:
        """List all registered services and their methods."""
        services = []
        
        for service_name, service_descriptor in self._service_descriptors.items():
            methods = []
            
            for method in service_descriptor.methods:
                methods.append({
                    "name": method.name,
                    "input_type": method.input_type.full_name,
                    "output_type": method.output_type.full_name,
                    "client_streaming": method.client_streaming,
                    "server_streaming": method.server_streaming,
                })
            
            services.append({
                "name": service_name,
                "methods": methods,
            })
        
        return services
    
    def validate_method_input(self, service_name: str, method_name: str, 
                             input_data: Union[Dict[str, Any], Message]) -> Message:
        """Validate input data for a specific service method."""
        method_descriptor = self.validate_service_method(service_name, method_name)
        
        # Get the input message type
        input_type_name = method_descriptor.input_type.full_name
        input_message_class = self.get_message_type(input_type_name)
        
        if not input_message_class:
            raise ValidationError(f"Input message type '{input_type_name}' not registered")
        
        # Convert input data to protobuf message if needed
        if isinstance(input_data, dict):
            input_message = self.json_to_proto(input_data, input_message_class)
        elif isinstance(input_data, Message):
            # Validate that it's the correct type
            if not isinstance(input_data, input_message_class):
                raise ValidationError(
                    f"Input message type mismatch. Expected {input_type_name}, "
                    f"got {input_data.DESCRIPTOR.full_name}"
                )
            input_message = input_data
            self.validate_message(input_message)
        else:
            raise ValidationError("Input data must be a dict or Protocol Buffer message")
        
        return input_message 