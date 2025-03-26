# XSD to JSON Schema Converter

A robust tool for converting XML Schema Definition (XSD) files to JSON Schema format. The converter supports a wide variety of XSD constructs and produces compliant JSON Schema documents.

## Features

- Convert XSD files to JSON Schema using ElementTree
- Support for simple and complex types
- Handling of attributes, enumerations, and restrictions
- Type mapping from XSD to JSON Schema
- Conversion via a user-friendly Streamlit web interface
- Download converted JSON Schemas

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install with development dependencies for testing:

```bash
pip install -e ".[dev]"
```

## Usage

### Web Interface

Run the Streamlit application:

```bash
streamlit run app.py
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

- `app.py` - Streamlit web application for user interface
- `xsd_converter.py` - Core conversion logic
- `tests/` - Unit tests
  - `test_xsd_converter.py` - Test cases for the converter
  - `resources/` - XSD files used in testing
    - `simple.xsd` - Basic XSD with element and attributes
    - `complex.xsd` - More complex structure with nested elements
    - `types.xsd` - Various data type examples
    - `restrictions.xsd` - Examples with restrictions and validations
    - `advanced.xsd` - Complex nested structures and relations
    - `ibm_example.xsd` - Sample from IBM documentation

## Implementation Details

The converter works by:
1. Parsing the XSD document using ElementTree
2. Mapping XSD elements and attributes to JSON Schema properties
3. Converting types according to a predefined mapping
4. Handling restrictions like minLength, maxLength, patterns, etc.
5. Processing enumerations and translating them to JSON Schema enum values
6. Preserving the hierarchical structure of complex types

## Development and Testing

Run tests with pytest:

```bash
python -m pytest
```

Tests verify the converter's functionality against various XSD structures:
- Simple elements with attributes
- Complex nested structures
- Different data types
- Restrictions and validations
- Enumerations
- Advanced structures

## License

[MIT License](LICENSE)
