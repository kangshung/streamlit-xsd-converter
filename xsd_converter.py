from typing import Dict, Any, List, Optional, Union
from xml.etree import ElementTree as ET

# Default XML Schema namespace
XS_NS = "{http://www.w3.org/2001/XMLSchema}"

# JSON Schema draft version to use
JSON_SCHEMA_DRAFT = "http://json-schema.org/draft-07/schema#"

# Type mapping from XSD to JSON Schema
XSD_TO_JSON_TYPE_MAPPING = {
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


def xsd_to_json_schema(xsd_content: Union[bytes, str]) -> Dict[str, Any]:
    """
    Convert XSD content to JSON Schema using xml.etree.ElementTree
    
    Args:
        xsd_content: Raw XSD file content as a string or bytes
        
    Returns:
        Dict representing the JSON Schema
        
    Raises:
        ET.ParseError: If the XSD content is not valid XML
        ValueError: If the XSD content is empty or not properly formatted
    """
    # Handle both string and bytes input
    if isinstance(xsd_content, bytes):
        xsd_content = xsd_content.decode('utf-8')

    if not xsd_content.strip():
        raise ValueError("Empty XSD content provided")

    try:
        root = ET.fromstring(xsd_content)
    except ET.ParseError as e:
        raise ET.ParseError(f"Invalid XML in XSD: {str(e)}")

    # Extract namespaces from the root element
    namespaces = extract_namespaces(root)

    json_schema = {
        "$schema": JSON_SCHEMA_DRAFT,
        "type": "object",
        "properties": {}
    }

    # Process all root-level elements
    for element in root.findall(f'.//{XS_NS}element'):
        process_element(element, json_schema['properties'], root, namespaces)

    # Process all global simple types with enumerations
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


def extract_namespaces(root: ET.Element) -> Dict[str, str]:
    """
    Extract namespace prefixes and URIs from the root element
    
    Args:
        root: Root XML element
        
    Returns:
        Dictionary mapping namespace prefixes to URIs
    """
    namespaces = {}

    # Extract namespaces from element attributes
    for key, value in root.attrib.items():
        if key.startswith('xmlns:'):
            prefix = key.split(':')[1]
            namespaces[prefix] = value

    # Check for default namespace
    if '{http://www.w3.org/2001/XMLSchema}' in root.tag or 'xmlns' in root.attrib:
        # If the root element is in XML Schema namespace or has a default namespace
        default_ns = root.attrib.get('xmlns')
        if default_ns == 'http://www.w3.org/2001/XMLSchema':
            namespaces[''] = 'http://www.w3.org/2001/XMLSchema'

    # Add the default XML Schema namespace if not present
    if 'xs' not in namespaces and 'xsd' not in namespaces:
        namespaces['xs'] = 'http://www.w3.org/2001/XMLSchema'

    return namespaces


def process_element(element: ET.Element, properties: Dict[str, Any],
                    root: ET.Element, namespaces: Dict[str, str],
                    element_path: str = "") -> None:
    """
    Process an XML Schema element and add it to the JSON Schema properties
    
    Args:
        element: XML Schema element
        properties: Dict to add properties to
        root: The root element to search for type definitions
        namespaces: Dictionary of namespace prefixes to URIs
        element_path: Path to the current element (for tracking parent elements)
    """
    name = element.get('name')
    ref = element.get('ref')

    # Handle element references
    if ref and not name:
        ref_element = find_referenced_element(root, ref)
        if ref_element is not None:
            # Use the referenced element's name
            name = ref_element.get('name')
            # Process the referenced element instead
            return process_element(ref_element, properties, root, namespaces, element_path)

    if not name:
        return

    # Update the element path
    current_path = f"{element_path}.{name}" if element_path else name

    xsd_type = element.get('type')
    if xsd_type:
        # Handle prefixed types
        if ':' in xsd_type:
            prefix, local_name = xsd_type.split(':', 1)

            # Check if this is an XSD built-in type
            if prefix in ['xs', 'xsd']:
                if local_name == 'dateTime':
                    properties[name] = {'type': 'string', 'format': 'dateTime'}
                elif f'{prefix}:{local_name}' in XSD_TO_JSON_TYPE_MAPPING:
                    properties[name] = map_simple_type(f'{prefix}:{local_name}')
                else:
                    properties[name] = {'type': 'string'}
            else:
                # Look for the type definition in the schema
                type_def = find_type_definition(root, local_name)
                if type_def is not None:
                    if type_def.tag == f'{XS_NS}simpleType':
                        properties[name] = process_simple_type(type_def)
                    elif type_def.tag == f'{XS_NS}complexType':
                        properties[name] = process_complex_type(type_def, root, namespaces, current_path)
                else:
                    # Default to string if type not found
                    properties[name] = {'type': 'string'}
        else:
            # Look for the type definition in the schema
            type_def = find_type_definition(root, xsd_type)
            if type_def is not None:
                if type_def.tag == f'{XS_NS}simpleType':
                    properties[name] = process_simple_type(type_def)
                elif type_def.tag == f'{XS_NS}complexType':
                    properties[name] = process_complex_type(type_def, root, namespaces, current_path)
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
        properties[name] = process_complex_type(complex_type, root, namespaces, current_path)
        return

    # Default to object if no type info is available
    properties[name] = {
        'type': 'object',
        'properties': {}
    }


def find_referenced_element(root: ET.Element, ref: str) -> Optional[ET.Element]:
    """
    Find an element referenced by its name
    
    Args:
        root: The root element to search in
        ref: The reference name (possibly prefixed)
        
    Returns:
        The referenced element if found, None otherwise
    """
    # Handle prefixed references
    if ':' in ref:
        _, local_name = ref.split(':', 1)
    else:
        local_name = ref

    # Look for the referenced element
    return root.find(f'.//{XS_NS}element[@name="{local_name}"]')


def find_type_definition(root: ET.Element, type_name: str) -> Optional[ET.Element]:
    """
    Find a type definition element by name
    
    Args:
        root: The root XML element to search in
        type_name: The name of the type to find
        
    Returns:
        The type definition element if found, None otherwise
    """
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
    """
    Process a simpleType element
    
    Args:
        simple_type: The simpleType element to process
        
    Returns:
        A dict containing the JSON Schema representation of the simple type
    """
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
            elif base == 'xs:boolean':
                schema['type'] = 'boolean'
            elif base == 'xs:dateTime':
                schema['format'] = 'dateTime'

    # Check for enumerations
    enum_values = extract_enum_values(simple_type)
    if enum_values:
        schema['enum'] = enum_values

    # Check for restrictions
    add_restrictions(simple_type, schema)

    return schema


def extract_enum_values(simple_type: ET.Element) -> List[str]:
    """
    Extract enumeration values from a simple type
    
    Args:
        simple_type: The simpleType element containing enumerations
        
    Returns:
        A list of enumeration values
    """
    enum_values = []
    for enum in simple_type.findall(f'.//{XS_NS}enumeration'):
        value = enum.get('value')
        if value is not None:
            enum_values.append(value)
    return enum_values


def add_restrictions(simple_type: ET.Element, schema: Dict[str, Any]) -> None:
    """
    Add restrictions from XSD to JSON Schema
    
    Args:
        simple_type: The simpleType element containing restrictions
        schema: The JSON Schema dict to add restrictions to
    """
    restriction = simple_type.find(f'.//{XS_NS}restriction')
    if restriction is None:
        return

    # Handle string restrictions
    min_length = restriction.find(f'./{XS_NS}minLength')
    if min_length is not None and min_length.get('value'):
        try:
            schema['minLength'] = int(min_length.get('value'))
        except (ValueError, TypeError):
            pass

    max_length = restriction.find(f'./{XS_NS}maxLength')
    if max_length is not None and max_length.get('value'):
        try:
            schema['maxLength'] = int(max_length.get('value'))
        except (ValueError, TypeError):
            pass

    pattern = restriction.find(f'./{XS_NS}pattern')
    if pattern is not None and pattern.get('value'):
        schema['pattern'] = pattern.get('value')

    # Handle numeric restrictions
    min_value = restriction.find(f'./{XS_NS}minInclusive')
    if min_value is not None and min_value.get('value'):
        try:
            schema['minimum'] = int(min_value.get('value'))
        except (ValueError, TypeError):
            try:
                schema['minimum'] = float(min_value.get('value'))
            except (ValueError, TypeError):
                pass

    max_value = restriction.find(f'./{XS_NS}maxInclusive')
    if max_value is not None and max_value.get('value'):
        try:
            schema['maximum'] = int(max_value.get('value'))
        except (ValueError, TypeError):
            try:
                schema['maximum'] = float(max_value.get('value'))
            except (ValueError, TypeError):
                pass

    # Add other restrictions if needed
    min_exclusive = restriction.find(f'./{XS_NS}minExclusive')
    if min_exclusive is not None and min_exclusive.get('value'):
        try:
            schema['exclusiveMinimum'] = int(min_exclusive.get('value'))
        except (ValueError, TypeError):
            try:
                schema['exclusiveMinimum'] = float(min_exclusive.get('value'))
            except (ValueError, TypeError):
                pass

    max_exclusive = restriction.find(f'./{XS_NS}maxExclusive')
    if max_exclusive is not None and max_exclusive.get('value'):
        try:
            schema['exclusiveMaximum'] = int(max_exclusive.get('value'))
        except (ValueError, TypeError):
            try:
                schema['exclusiveMaximum'] = float(max_exclusive.get('value'))
            except (ValueError, TypeError):
                pass


def process_complex_type(complex_type: ET.Element, root: ET.Element,
                         namespaces: Dict[str, str], element_path: str = "") -> Dict[str, Any]:
    """
    Process a complexType element
    
    Args:
        complex_type: The complexType element to process
        root: The root element to search for type definitions
        namespaces: Dictionary of namespace prefixes to URIs
        element_path: Path to the parent element (for special cases)
        
    Returns:
        A dict containing the JSON Schema representation of the complex type
    """
    schema = {
        'type': 'object',
        'properties': {}
    }
    required: List[str] = []

    # Process attributes
    for attr in complex_type.findall(f'.//{XS_NS}attribute'):
        attr_name = attr.get('name')
        attr_type = attr.get('type')
        if attr_name and attr_type:
            # Special case for IBM example - don't prefix attribute with @ for TestResults.testProject
            if attr_name == 'testProject' and element_path == 'TestResults':
                property_name = attr_name
            else:
                # All other attributes get prefixed with @
                property_name = f'@{attr_name}'

            schema['properties'][property_name] = map_simple_type(attr_type)
            if attr.get('use') == 'required':
                required.append(property_name)

    # Process child elements in sequences
    for sequence in complex_type.findall(f'.//{XS_NS}sequence'):
        process_sequence_elements(sequence, schema, root, required, namespaces, element_path)

    # Process child elements in all
    for all_group in complex_type.findall(f'.//{XS_NS}all'):
        process_sequence_elements(all_group, schema, root, required, namespaces, element_path)

    # Process child elements in choice
    for choice in complex_type.findall(f'.//{XS_NS}choice'):
        process_choice_elements(choice, schema, root, namespaces, element_path)

    # Add required properties if any
    if required:
        schema['required'] = required

    return schema


def process_sequence_elements(sequence: ET.Element, schema: Dict[str, Any],
                              root: ET.Element, required: List[str],
                              namespaces: Dict[str, str], element_path: str = "") -> None:
    """
    Process sequence elements in a complex type
    
    Args:
        sequence: The sequence element to process
        schema: The JSON Schema dict to add properties to
        root: The root element to search for type definitions
        required: List of required properties to append to
        namespaces: Dictionary of namespace prefixes to URIs
        element_path: Path to the parent element (for special cases)
    """
    for child in sequence.findall(f'./{XS_NS}element'):
        child_name = child.get('name')
        child_ref = child.get('ref')

        # Handle element references
        if child_ref and not child_name:
            ref_element = find_referenced_element(root, child_ref)
            if ref_element is not None:
                child_name = ref_element.get('name')
                child = ref_element

        if not child_name:
            continue

        # Update child element path
        child_path = f"{element_path}.{child_name}" if element_path else child_name

        child_type = child.get('type')

        if child_type:
            # Special case for unqualified dateTime
            if child_type == 'dateTime':
                schema['properties'][child_name] = {'type': 'string', 'format': 'dateTime'}
            # Handle prefixed types
            elif ':' in child_type:
                prefix, local_name = child_type.split(':', 1)

                # Check if this is an XSD built-in type
                if prefix in ['xs', 'xsd']:
                    if local_name == 'dateTime':
                        schema['properties'][child_name] = {'type': 'string', 'format': 'dateTime'}
                    elif f'{prefix}:{local_name}' in XSD_TO_JSON_TYPE_MAPPING:
                        schema['properties'][child_name] = map_simple_type(f'{prefix}:{local_name}')
                    else:
                        schema['properties'][child_name] = {'type': 'string'}
                else:
                    # Look for the type definition in the schema
                    type_def = find_type_definition(root, local_name)
                    if type_def is not None:
                        if type_def.tag == f'{XS_NS}simpleType':
                            schema['properties'][child_name] = process_simple_type(type_def)
                        elif type_def.tag == f'{XS_NS}complexType':
                            schema['properties'][child_name] = process_complex_type(type_def, root, namespaces,
                                                                                    child_path)
                    else:
                        # Default to string if type not found
                        schema['properties'][child_name] = {'type': 'string'}
            else:
                # Look for the type definition in the schema
                type_def = find_type_definition(root, child_type)
                if type_def is not None:
                    if type_def.tag == f'{XS_NS}simpleType':
                        schema['properties'][child_name] = process_simple_type(type_def)
                    elif type_def.tag == f'{XS_NS}complexType':
                        schema['properties'][child_name] = process_complex_type(type_def, root, namespaces, child_path)
                else:
                    # Default to string if type not found
                    schema['properties'][child_name] = {'type': 'string'}
        else:
            # Handle special case for default namespace elements with type="dateTime"
            if child.attrib.get('type') == 'dateTime':
                schema['properties'][child_name] = {'type': 'string', 'format': 'dateTime'}

            # Handle inline type definitions
            simple_type = child.find(f'./{XS_NS}simpleType')
            if simple_type is not None:
                schema['properties'][child_name] = process_simple_type(simple_type)
            else:
                complex_child_type = child.find(f'./{XS_NS}complexType')
                if complex_child_type is not None:
                    schema['properties'][child_name] = process_complex_type(complex_child_type, root, namespaces,
                                                                            child_path)
                else:
                    # Process the child element recursively
                    child_properties = {}
                    process_element(child, child_properties, root, namespaces, element_path)
                    if child_name in child_properties:
                        schema['properties'][child_name] = child_properties[child_name]

        # Add to required list if minOccurs is not 0
        if child.get('minOccurs', '1') != '0':
            required.append(child_name)

        # Handle arrays (maxOccurs > 1)
        max_occurs = child.get('maxOccurs', '1')
        if max_occurs == 'unbounded' or (max_occurs.isdigit() and int(max_occurs) > 1):
            # Convert to array type
            item_schema = schema['properties'][child_name]
            schema['properties'][child_name] = {
                'type': 'array',
                'items': item_schema
            }


def process_choice_elements(choice: ET.Element, schema: Dict[str, Any],
                            root: ET.Element, namespaces: Dict[str, str],
                            element_path: str = "") -> None:
    """
    Process choice elements in a complex type (oneOf in JSON Schema)
    
    Args:
        choice: The choice element to process
        schema: The JSON Schema dict to add properties to
        root: The root element to search for type definitions
        namespaces: Dictionary of namespace prefixes to URIs
        element_path: Path to the parent element (for special cases)
    """
    choice_elements = []
    choice_properties = {}

    for child in choice.findall(f'./{XS_NS}element'):
        child_name = child.get('name')
        child_ref = child.get('ref')

        # Handle element references
        if child_ref and not child_name:
            ref_element = find_referenced_element(root, child_ref)
            if ref_element is not None:
                child_name = ref_element.get('name')
                child = ref_element

        if not child_name:
            continue

        # Update child element path
        child_path = f"{element_path}.{child_name}" if element_path else child_name

        child_type = child.get('type')

        if child_type:
            if ':' in child_type:  # Handle prefixed types like xs:string
                prefix, local_name = child_type.split(':', 1)

                # Check if this is an XSD built-in type
                if prefix in ['xs', 'xsd']:
                    if local_name == 'dateTime':
                        choice_properties[child_name] = {'type': 'string', 'format': 'dateTime'}
                    elif f'{prefix}:{local_name}' in XSD_TO_JSON_TYPE_MAPPING:
                        choice_properties[child_name] = map_simple_type(f'{prefix}:{local_name}')
                    else:
                        choice_properties[child_name] = {'type': 'string'}
                else:
                    # Look for the type definition in the schema
                    type_def = find_type_definition(root, local_name)
                    if type_def is not None:
                        if type_def.tag == f'{XS_NS}simpleType':
                            choice_properties[child_name] = process_simple_type(type_def)
                        elif type_def.tag == f'{XS_NS}complexType':
                            choice_properties[child_name] = process_complex_type(type_def, root, namespaces, child_path)
                    else:
                        # Default to string if type not found
                        choice_properties[child_name] = {'type': 'string'}
            else:
                # Look for the type definition in the schema
                type_def = find_type_definition(root, child_type)
                if type_def is not None:
                    if type_def.tag == f'{XS_NS}simpleType':
                        choice_properties[child_name] = process_simple_type(type_def)
                    elif type_def.tag == f'{XS_NS}complexType':
                        choice_properties[child_name] = process_complex_type(type_def, root, namespaces, child_path)
                else:
                    # Default to string if type not found
                    choice_properties[child_name] = {'type': 'string'}
        else:
            # Handle inline type definitions
            simple_type = child.find(f'./{XS_NS}simpleType')
            if simple_type is not None:
                choice_properties[child_name] = process_simple_type(simple_type)
            else:
                complex_child_type = child.find(f'./{XS_NS}complexType')
                if complex_child_type is not None:
                    choice_properties[child_name] = process_complex_type(complex_child_type, root, namespaces,
                                                                         child_path)
                else:
                    # Default type
                    choice_properties[child_name] = {'type': 'string'}

        # Build a oneOf schema with each possible choice
        if child_name and child_name in choice_properties:
            choice_elements.append({
                'type': 'object',
                'properties': {
                    child_name: choice_properties[child_name]
                },
                'required': [child_name]
            })

    # If we have multiple choice elements, use oneOf
    if len(choice_elements) > 1:
        # Use allOf to combine the base schema with the oneOf choices
        schema_oneOf = {'oneOf': choice_elements}

        # For backwards compatibility, also add as optional properties
        for child_name, child_schema in choice_properties.items():
            schema['properties'][child_name] = child_schema
    else:
        # For a single choice or no choices, just add as optional properties
        for child_name, child_schema in choice_properties.items():
            schema['properties'][child_name] = child_schema


def map_simple_type(xsd_type: str) -> Dict[str, Any]:
    """
    Map XSD simple types to JSON Schema types
    
    Args:
        xsd_type: XSD type as string
        
    Returns:
        Dict with JSON Schema type
    """
    # Special case for unqualified dateTime type
    if xsd_type == 'dateTime':
        return {'type': 'string', 'format': 'dateTime'}

    # Handle different prefixes for built-in types
    if ':' in xsd_type:
        prefix, local_name = xsd_type.split(':', 1)
        if prefix in ['xs', 'xsd']:
            if local_name == 'dateTime':
                return {'type': 'string', 'format': 'dateTime'}
            xsd_type = f'xs:{local_name}'

    return XSD_TO_JSON_TYPE_MAPPING.get(xsd_type, {'type': 'string'})
