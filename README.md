# XSD to JSON Schema Converter

A robust tool for converting XML Schema Definition (XSD) files to JSON Schema format. The converter supports a wide variety of XSD constructs and produces compliant JSON Schema documents.

## Features

- Convert XSD files to JSON Schema using ElementTree
- Support for simple and complex types
- Handling of attributes, enumerations, and restrictions
- Type mapping from XSD to JSON Schema
- Support for namespaces and element references
- Support for arrays (maxOccurs)
- Support for choice elements
- Conversion via a user-friendly Streamlit web interface
- Download converted JSON Schemas

## Installation

1. Clone this repository
2. Install the required dependencies using [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -e .
```

## Usage

### Web Interface

Run the Streamlit application:

```bash
uv run streamlit run app.py
```

Then:
1. Open the displayed URL in your web browser
2. Upload an XSD file
3. Convert to JSON Schema
4. Preview and download the result

### Programmatic Usage

You can also use the converter programmatically:

```python
from xsd_converter import xsd_to_json_schema

# Read an XSD file
with open('schema.xsd', 'rb') as f:
    xsd_content = f.read()

# Convert to JSON Schema
json_schema = xsd_to_json_schema(xsd_content)

# Use the result
import json
print(json.dumps(json_schema, indent=2))
```

## Project Structure

```
streamlit-xsd-converter/
├── app.py                  # Streamlit web application
├── xsd_converter.py        # Core conversion logic
├── pyproject.toml          # Project configuration
├── uv.lock                 # uv dependency lock file
├── LICENSE                 # License file
├── README.md               # This file
└── tests/                  # Unit tests
    ├── __init__.py
    ├── test_xsd_converter.py  # Test cases for the converter
    └── resources/          # XSD files used in testing
        ├── advanced.xsd    # Complex nested structures and relations
        ├── array_test.xsd  # Array handling test (maxOccurs)  
        ├── choice_test.xsd # Choice element handling test
        ├── complex.xsd     # Complex structure with nested elements
        ├── ibm_example.xsd # Sample from IBM documentation
        ├── namespace_test.xsd # Namespace and reference handling test
        ├── restrictions.xsd   # Restrictions and validations
        ├── simple.xsd      # Basic XSD with element and attributes
        └── types.xsd       # Various data type examples
```

## Implementation Details

The converter works by:
1. Parsing the XSD document using ElementTree
2. Extracting namespaces and handling references
3. Mapping XSD elements and attributes to JSON Schema properties
4. Converting types according to a predefined mapping
5. Handling restrictions like minLength, maxLength, patterns, etc.
6. Processing enumerations and translating them to JSON Schema enum values
7. Preserving the hierarchical structure of complex types
8. Handling arrays through maxOccurs attribute
9. Supporting choice elements

## Development and Testing

Run tests with pytest:

```bash
uv run pytest
```

Tests verify the converter's functionality against various XSD structures:
- Simple elements with attributes
- Complex nested structures
- Different data types
- Restrictions and validations
- Enumerations
- Arrays (maxOccurs)
- Namespaces and element references
- Choice elements

## License

[MIT License](LICENSE)
