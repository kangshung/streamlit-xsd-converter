import os
import json
import pytest
from pathlib import Path
from xsd_converter import xsd_to_json_schema

# Test directory
TEST_DIR = Path(__file__).parent
RESOURCES_DIR = TEST_DIR / "resources"
os.makedirs(RESOURCES_DIR, exist_ok=True)

def read_resource_file(filename):
    """Read a resource file from the resources directory"""
    file_path = RESOURCES_DIR / filename
    with open(file_path, 'rb') as f:
        return f.read()

def test_simple_xsd_conversion():
    """Test conversion of a simple XSD file"""
    # Load XSD from resources
    xsd_content = read_resource_file("simple.xsd")
    
    # Convert the XSD to JSON Schema
    schema = xsd_to_json_schema(xsd_content)
    
    # Basic assertions
    assert schema is not None
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "person" in schema["properties"]
    
    # Check person element structure
    person = schema["properties"]["person"]
    assert person["type"] == "object"
    assert "properties" in person
    
    # Check attributes and elements
    properties = person["properties"]
    assert "@id" in properties
    assert properties["@id"]["type"] == "string"
    assert "firstName" in properties
    assert properties["firstName"]["type"] == "string"
    assert "lastName" in properties
    assert properties["lastName"]["type"] == "string"
    assert "age" in properties
    assert properties["age"]["type"] == "integer"
    
    # Check required fields
    assert "required" in person
    assert "@id" in person["required"]
    assert "firstName" in person["required"]
    assert "lastName" in person["required"]
    assert "age" not in person["required"]  # Optional element


def test_complex_xsd_conversion():
    """Test conversion of a more complex XSD file"""
    # Load XSD from resources
    xsd_content = read_resource_file("complex.xsd")
    
    # Convert the XSD to JSON Schema
    schema = xsd_to_json_schema(xsd_content)
    
    # Basic assertions
    assert schema is not None
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "order" in schema["properties"]
    
    # Check order element structure
    order = schema["properties"]["order"]
    assert order["type"] == "object"
    assert "properties" in order
    
    # Check nested elements
    properties = order["properties"]
    assert "customer" in properties
    assert "items" in properties
    assert "totalCost" in properties
    assert "@id" in properties
    assert "@orderDate" in properties
    
    # Check data types
    assert properties["totalCost"]["type"] == "number"
    assert properties["@orderDate"].get("format") == "date"


def test_data_types_conversion():
    """Test conversion of different XSD data types"""
    # Load XSD from resources
    xsd_content = read_resource_file("types.xsd")
    
    # Convert the XSD to JSON Schema
    schema = xsd_to_json_schema(xsd_content)
    
    # Get data properties
    data_properties = schema["properties"]["data"]["properties"]
    
    # Check type mappings
    assert data_properties["string"]["type"] == "string"
    assert data_properties["integer"]["type"] == "integer"
    assert data_properties["decimal"]["type"] == "number"
    assert data_properties["boolean"]["type"] == "boolean"
    assert data_properties["date"]["type"] == "string"
    assert data_properties["date"].get("format") == "date"
    assert data_properties["time"]["type"] == "string"
    assert data_properties["time"].get("format") == "time"
    assert data_properties["dateTime"]["type"] == "string"
    assert data_properties["dateTime"].get("format") == "dateTime"


def test_restrictions_conversion():
    """Test conversion of XSD restrictions"""
    # Load XSD from resources
    xsd_content = read_resource_file("restrictions.xsd")
    
    # Convert the XSD to JSON Schema
    schema = xsd_to_json_schema(xsd_content)
    
    # Get user properties
    user_properties = schema["properties"]["user"]["properties"]
    
    # Check username restrictions
    username = user_properties["username"]
    assert username["type"] == "string"
    assert "minLength" in username
    assert username["minLength"] == 3
    assert "maxLength" in username
    assert username["maxLength"] == 20
    assert "pattern" in username
    
    # Check age restrictions
    age = user_properties["age"]
    assert age["type"] == "integer"
    assert "minimum" in age
    assert age["minimum"] == 18
    assert "maximum" in age
    assert age["maximum"] == 120
    
    # Check enum
    user_type = user_properties["userType"]
    assert user_type["type"] == "string"
    assert "enum" in user_type
    assert set(user_type["enum"]) == {"admin", "user", "guest"}


def test_advanced_xsd_conversion():
    """Test conversion of an advanced XSD with complex types"""
    # Load XSD from resources
    xsd_content = read_resource_file("advanced.xsd")
    
    # Convert the XSD to JSON Schema
    schema = xsd_to_json_schema(xsd_content)
    
    # Basic assertions
    assert schema is not None
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "customer" in schema["properties"]
    
    # Check customer element
    customer = schema["properties"]["customer"]
    assert customer["type"] == "object"
    assert "properties" in customer
    
    # Check attributes
    customer_props = customer["properties"]
    assert "@id" in customer_props
    assert customer_props["@id"]["type"] == "string"
    assert "@customerSince" in customer_props
    assert customer_props["@customerSince"]["type"] == "string"
    assert customer_props["@customerSince"].get("format") == "date"
    
    # Check nested personalInfo
    assert "personalInfo" in customer_props
    personal_info = customer_props["personalInfo"]
    assert personal_info["type"] == "object"
    assert "properties" in personal_info
    
    # Check personal info properties
    pi_props = personal_info["properties"]
    assert "firstName" in pi_props
    assert "lastName" in pi_props
    assert "email" in pi_props
    assert "phone" in pi_props
    assert "birthDate" in pi_props
    assert pi_props["birthDate"]["format"] == "date"
    
    # Check preferences
    assert "preferences" in customer_props
    prefs = customer_props["preferences"]
    assert prefs["type"] == "object"
    assert "properties" in prefs
    
    # Check preferences properties
    pref_props = prefs["properties"]
    assert "contactMethod" in pref_props
    assert "enum" in pref_props["contactMethod"]
    assert set(pref_props["contactMethod"]["enum"]) == {"email", "phone", "mail"}
    assert "frequency" in pref_props
    assert "newsletter" in pref_props
    assert pref_props["newsletter"]["type"] == "boolean"


def test_ibm_example_xsd_conversion():
    """Test conversion of the IBM example XSD file."""
    xsd_content = read_resource_file('ibm_example.xsd')
    json_schema = xsd_to_json_schema(xsd_content)
    assert json_schema is not None
    assert 'TestResults' in json_schema['properties']
    assert 'testSuites' in json_schema['properties']['TestResults']['properties']
    assert 'testProject' in json_schema['properties']['TestResults']['properties']
    assert 'Severity' in json_schema['properties']
    assert 'pass' in json_schema['properties']['Severity']['enum']
    assert 'fail' in json_schema['properties']['Severity']['enum']
    assert 'error' in json_schema['properties']['Severity']['enum']

# Add the new test to the test suite 