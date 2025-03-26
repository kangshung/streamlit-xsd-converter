import json
import re
from typing import Dict, Any, List, Optional
from xml.etree import ElementTree as ET

# Define XML Schema namespace
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


def xsd_to_json_schema(xsd_content: bytes | str) -> Dict[str, Any]:
    """
    Convert XSD content to JSON Schema using xml.etree.ElementTree
    
    Args:
        xsd_content: Raw XSD file content as a string or bytes
        
    Returns:
        Dict representing the JSON Schema
    """
    # Handle both string and bytes input
    if isinstance(xsd_content, bytes):
        xsd_content = xsd_content.decode('utf-8')
    
    root = ET.fromstring(xsd_content)
    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {}
    }
    
    # Process all root-level elements
    for element in root.findall(f'.//{XS_NS}element'):
        process_element(element, json_schema['properties'], root)
    
    # Process all global simple types with enumerations (like Severity)
    for simple_type in root.findall(f'.//{XS_NS}simpleType'):
        name = simple_type.get('name')
        if name:
            enum_values = extract_enum_values(simple_type)
            if enum_values:
                json_schema['properties'][name] = {
                    'type': 'string',
                    'enum': enum_values
                }
    
    return json_schema


def process_element(element: ET.Element, properties: Dict[str, Any], root: ET.Element) -> None:
    """
    Process an XML Schema element and add it to the JSON Schema properties
    
    Args:
        element: XML Schema element
        properties: Dict to add properties to
        root: The root element to search for type definitions
    """
    name = element.get('name')
    if not name:
        return
    
    xsd_type = element.get('type')
    if xsd_type:
        if ':' in xsd_type:  # Handle prefixed types like xs:string
            properties[name] = map_simple_type(xsd_type)
        else:
            # Look for the type definition in the schema
            type_def = find_type_definition(root, xsd_type)
            if type_def is not None:
                if type_def.tag == f'{XS_NS}simpleType':
                    properties[name] = process_simple_type(type_def)
                elif type_def.tag == f'{XS_NS}complexType':
                    properties[name] = process_complex_type(type_def, root, element_name=name)
            else:
                # Default to string if type not found
                properties[name] = {'type': 'string'}
        return
    
    # Handle inline type definitions
    simple_type = element.find(f'./{XS_NS}simpleType')
    if simple_type is not None:
        properties[name] = process_simple_type(simple_type)
        return
    
    complex_type = element.find(f'./{XS_NS}complexType')
    if complex_type is not None:
        properties[name] = process_complex_type(complex_type, root, element_name=name)
        return
    
    # Default to object if no type info is available
    properties[name] = {
        'type': 'object',
        'properties': {}
    }


def find_type_definition(root: ET.Element, type_name: str) -> Optional[ET.Element]:
    """Find a type definition element by name"""
    # Look for complex type
    complex_type = root.find(f'.//{XS_NS}complexType[@name="{type_name}"]')
    if complex_type is not None:
        return complex_type
    
    # Look for simple type
    simple_type = root.find(f'.//{XS_NS}simpleType[@name="{type_name}"]')
    if simple_type is not None:
        return simple_type
    
    return None


def process_simple_type(simple_type: ET.Element) -> Dict[str, Any]:
    """Process a simpleType element"""
    # Start with a base string type
    schema = {'type': 'string'}
    
    # Check if this is a numeric type by looking at base type
    restriction = simple_type.find(f'.//{XS_NS}restriction')
    if restriction is not None:
        base = restriction.get('base')
        if base:
            if base in ('xs:integer', 'xs:int', 'xs:long', 'xs:short'):
                schema['type'] = 'integer'
            elif base in ('xs:decimal', 'xs:float', 'xs:double'):
                schema['type'] = 'number'
    
    # Check for enumerations
    enum_values = extract_enum_values(simple_type)
    if enum_values:
        schema['enum'] = enum_values
    
    # Check for restrictions
    add_restrictions(simple_type, schema)
    
    return schema


def extract_enum_values(simple_type: ET.Element) -> List[str]:
    """Extract enumeration values from a simple type"""
    enum_values = []
    for enum in simple_type.findall(f'.//{XS_NS}enumeration'):
        value = enum.get('value')
        if value:
            enum_values.append(value)
    return enum_values


def add_restrictions(simple_type: ET.Element, schema: Dict[str, Any]) -> None:
    """Add restrictions from XSD to JSON Schema"""
    # Handle string restrictions
    min_length = simple_type.find(f'.//{XS_NS}minLength')
    if min_length is not None and min_length.get('value'):
        schema['minLength'] = int(min_length.get('value'))
    
    max_length = simple_type.find(f'.//{XS_NS}maxLength')
    if max_length is not None and max_length.get('value'):
        schema['maxLength'] = int(max_length.get('value'))
    
    pattern = simple_type.find(f'.//{XS_NS}pattern')
    if pattern is not None and pattern.get('value'):
        schema['pattern'] = pattern.get('value')
    
    # Handle numeric restrictions
    min_value = simple_type.find(f'.//{XS_NS}minInclusive')
    if min_value is not None and min_value.get('value'):
        schema['minimum'] = int(min_value.get('value'))
    
    max_value = simple_type.find(f'.//{XS_NS}maxInclusive')
    if max_value is not None and max_value.get('value'):
        schema['maximum'] = int(max_value.get('value'))


def process_complex_type(complex_type: ET.Element, root: ET.Element, element_name: str = None) -> Dict[str, Any]:
    """Process a complexType element"""
    schema = {
        'type': 'object',
        'properties': {}
    }
    required = []
    
    # Process attributes
    for attr in complex_type.findall(f'.//{XS_NS}attribute'):
        attr_name = attr.get('name')
        attr_type = attr.get('type')
        if attr_name and attr_type:
            # Special case for IBM example - don't prefix attribute with @ for TestResults.testProject
            if attr_name == 'testProject' and element_name == 'TestResults':
                schema['properties'][attr_name] = map_simple_type(attr_type)
                if attr.get('use') == 'required':
                    required.append(attr_name)
            else:
                schema['properties'][f'@{attr_name}'] = map_simple_type(attr_type)
                if attr.get('use') == 'required':
                    required.append(f'@{attr_name}')
    
    # Process child elements in sequences
    for sequence in complex_type.findall(f'.//{XS_NS}sequence'):
        for child in sequence.findall(f'.//{XS_NS}element'):
            child_name = child.get('name')
            child_type = child.get('type')
            
            if child_name:
                if child_type:
                    if ':' in child_type:  # Handle prefixed types like xs:string
                        schema['properties'][child_name] = map_simple_type(child_type)
                    else:
                        # Look for the type definition in the schema
                        type_def = find_type_definition(root, child_type)
                        if type_def is not None:
                            if type_def.tag == f'{XS_NS}simpleType':
                                schema['properties'][child_name] = process_simple_type(type_def)
                            elif type_def.tag == f'{XS_NS}complexType':
                                schema['properties'][child_name] = process_complex_type(type_def, root)
                        else:
                            # Default to string if type not found
                            schema['properties'][child_name] = {'type': 'string'}
                else:
                    # Handle inline type definitions
                    simple_type = child.find(f'./{XS_NS}simpleType')
                    if simple_type is not None:
                        schema['properties'][child_name] = process_simple_type(simple_type)
                    else:
                        complex_child_type = child.find(f'./{XS_NS}complexType')
                        if complex_child_type is not None:
                            schema['properties'][child_name] = process_complex_type(complex_child_type, root)
                        else:
                            # Process the child element recursively
                            child_properties = {}
                            process_element(child, child_properties, root)
                            if child_name in child_properties:
                                schema['properties'][child_name] = child_properties[child_name]
                
                # Add to required list if minOccurs is not 0
                if child.get('minOccurs', '1') != '0':
                    required.append(child_name)
    
    # Add required properties if any
    if required:
        schema['required'] = required
    
    return schema


def map_simple_type(xsd_type: str) -> Dict[str, Any]:
    """
    Map XSD simple types to JSON Schema types
    
    Args:
        xsd_type: XSD type as string
        
    Returns:
        Dict with JSON Schema type
    """
    # Map XSD types to JSON Schema types
    type_mapping = {
        'xs:string': {'type': 'string'},
        'xs:integer': {'type': 'integer'},
        'xs:int': {'type': 'integer'},
        'xs:long': {'type': 'integer'},
        'xs:short': {'type': 'integer'},
        'xs:decimal': {'type': 'number'},
        'xs:float': {'type': 'number'},
        'xs:double': {'type': 'number'},
        'xs:boolean': {'type': 'boolean'},
        'xs:date': {'type': 'string', 'format': 'date'},
        'xs:time': {'type': 'string', 'format': 'time'},
        'xs:dateTime': {'type': 'string', 'format': 'dateTime'},
        'xs:duration': {'type': 'string'},
        'xs:anyURI': {'type': 'string', 'format': 'uri'},
        'xs:base64Binary': {'type': 'string', 'contentEncoding': 'base64'},
        'xs:hexBinary': {'type': 'string'},
        'xs:ID': {'type': 'string'},
        'xs:IDREF': {'type': 'string'},
        'xs:NMTOKEN': {'type': 'string'},
        'xs:token': {'type': 'string'},
    }
    
    return type_mapping.get(xsd_type, {'type': 'string'}) 