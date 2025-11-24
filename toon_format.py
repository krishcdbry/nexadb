#!/usr/bin/env python3
"""
TOON Format Support for NexaDB
================================

Token-Oriented Object Notation (TOON) - A compact data format optimized for LLMs.
https://github.com/toon-format/toon

Key Features:
- 40% fewer tokens than JSON
- Better LLM comprehension (73.9% vs JSON's 69.7%)
- Tabular arrays with explicit schemas
- YAML-like indentation for nested objects

NexaDB is the FIRST database with native TOON support!
"""

import json
from typing import Any, Dict, List, Union


class TOONSerializer:
    """
    Serialize Python objects (JSON-like) to TOON format.

    Optimized for:
    - Uniform arrays of objects (best case)
    - Nested objects with indentation
    - Primitive arrays with length declarations
    """

    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size

    def serialize(self, data: Any, indent_level: int = 0) -> str:
        """
        Convert Python object to TOON format string.

        Args:
            data: Python object (dict, list, primitives)
            indent_level: Current indentation level

        Returns:
            TOON formatted string
        """
        if isinstance(data, dict):
            return self._serialize_object(data, indent_level)
        elif isinstance(data, list):
            return self._serialize_array(data, indent_level)
        else:
            return self._serialize_primitive(data)

    def _serialize_object(self, obj: Dict, indent_level: int) -> str:
        """Serialize dictionary to TOON object format"""
        lines = []
        indent = ' ' * (indent_level * self.indent_size)

        for key, value in obj.items():
            if isinstance(value, dict):
                # Nested object
                lines.append(f"{indent}{key}:")
                lines.append(self._serialize_object(value, indent_level + 1))
            elif isinstance(value, list):
                # Array
                lines.append(f"{indent}{self._serialize_array_with_key(key, value, indent_level)}")
            else:
                # Primitive
                lines.append(f"{indent}{key}: {self._serialize_primitive(value)}")

        return '\n'.join(lines)

    def _serialize_array(self, arr: List, indent_level: int) -> str:
        """Serialize list to TOON array format"""
        if not arr:
            return "[]"

        # Check if array of uniform objects (best case for TOON)
        if all(isinstance(item, dict) for item in arr):
            return self._serialize_tabular_array(arr, indent_level)

        # Check if array of primitives
        if all(not isinstance(item, (dict, list)) for item in arr):
            # Inline array for primitives
            serialized_items = [self._serialize_primitive(item) for item in arr]
            return ','.join(serialized_items)

        # Mixed array - serialize each item on new line
        indent = ' ' * (indent_level * self.indent_size)
        lines = []
        for item in arr:
            lines.append(f"{indent}{self.serialize(item, indent_level + 1)}")
        return '\n'.join(lines)

    def _serialize_array_with_key(self, key: str, arr: List, indent_level: int) -> str:
        """Serialize array with key prefix"""
        if not arr:
            return f"{key}[0]:"

        length = len(arr)

        # Check if uniform objects (tabular format)
        if all(isinstance(item, dict) for item in arr):
            # Get all unique keys across all objects
            all_keys = []
            seen = set()
            for item in arr:
                for k in item.keys():
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)

            if all_keys:
                # Tabular format: key[N]{field1,field2,...}:
                fields = ','.join(all_keys)
                indent = ' ' * ((indent_level + 1) * self.indent_size)

                lines = [f"{key}[{length}]{{{fields}}}:"]

                # Add rows
                for item in arr:
                    row_values = []
                    for field in all_keys:
                        value = item.get(field)
                        row_values.append(self._serialize_primitive(value))
                    lines.append(f"{indent}{','.join(row_values)}")

                return '\n'.join(lines)

        # Primitive array
        if all(not isinstance(item, (dict, list)) for item in arr):
            serialized_items = [self._serialize_primitive(item) for item in arr]
            return f"{key}[{length}]: {','.join(serialized_items)}"

        # Mixed array - one item per line
        lines = [f"{key}[{length}]:"]
        indent = ' ' * ((indent_level + 1) * self.indent_size)
        for item in arr:
            lines.append(f"{indent}{self.serialize(item, indent_level + 1)}")
        return '\n'.join(lines)

    def _serialize_tabular_array(self, arr: List[Dict], indent_level: int) -> str:
        """Serialize uniform array of objects in tabular format"""
        if not arr:
            return ""

        # Get all unique keys
        all_keys = []
        seen = set()
        for item in arr:
            for k in item.keys():
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)

        fields = ','.join(all_keys)
        indent = ' ' * (indent_level * self.indent_size)

        lines = []
        for item in arr:
            row_values = []
            for field in all_keys:
                value = item.get(field)
                row_values.append(self._serialize_primitive(value))
            lines.append(f"{indent}{','.join(row_values)}")

        return '\n'.join(lines)

    def _serialize_primitive(self, value: Any) -> str:
        """Serialize primitive value"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Escape commas and newlines in strings
            if ',' in value or '\n' in value or '"' in value:
                # Use JSON string escaping
                return json.dumps(value)
            return value
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)


class TOONParser:
    """
    Parse TOON format to Python objects (JSON-like).

    Handles:
    - Tabular arrays with field declarations
    - Nested objects with indentation
    - Primitive arrays and values
    """

    def parse(self, toon_str: str) -> Any:
        """
        Parse TOON format string to Python object.

        Args:
            toon_str: TOON formatted string

        Returns:
            Python object (dict, list, or primitive)
        """
        lines = toon_str.strip().split('\n')
        result, _ = self._parse_lines(lines, 0, 0)
        return result

    def _parse_lines(self, lines: List[str], start_idx: int, base_indent: int) -> tuple:
        """
        Parse lines recursively.

        Returns:
            (parsed_object, next_line_index)
        """
        obj = {}
        idx = start_idx

        while idx < len(lines):
            line = lines[idx]

            # Skip empty lines
            if not line.strip():
                idx += 1
                continue

            # Calculate indentation
            indent = len(line) - len(line.lstrip())

            # If indentation decreases, return (end of current object)
            if indent < base_indent:
                break

            # If indentation is greater, skip (handled by nested call)
            if indent > base_indent:
                idx += 1
                continue

            line_content = line.strip()

            # Check for key-value pair
            if ':' in line_content:
                key, value_part = line_content.split(':', 1)
                key = key.strip()
                value_part = value_part.strip()

                # Check for array declaration: key[N] or key[N]{fields}
                if '[' in key and ']' in key:
                    array_key, array_meta = self._parse_array_declaration(key)

                    # Check if tabular array
                    if '{' in key:
                        # Tabular array: parse rows
                        fields = array_meta['fields']
                        length = array_meta['length']

                        # Parse rows
                        rows = []
                        row_idx = idx + 1
                        row_indent = indent + 2  # Expected indentation for rows

                        while row_idx < len(lines) and len(rows) < length:
                            row_line = lines[row_idx]
                            row_line_indent = len(row_line) - len(row_line.lstrip())

                            if row_line_indent >= row_indent and row_line.strip():
                                row_values = self._parse_csv_row(row_line.strip())

                                # Map values to fields
                                row_obj = {}
                                for field_idx, field in enumerate(fields):
                                    if field_idx < len(row_values):
                                        row_obj[field] = self._parse_primitive(row_values[field_idx])

                                rows.append(row_obj)

                            row_idx += 1

                        obj[array_key] = rows
                        idx = row_idx
                        continue
                    else:
                        # Primitive array: key[N]: val1,val2,val3
                        if value_part:
                            values = self._parse_csv_row(value_part)
                            obj[array_key] = [self._parse_primitive(v) for v in values]
                        else:
                            obj[array_key] = []
                        idx += 1
                        continue
                elif not value_part:
                    # Key without value - check if next line is indented (nested object)
                    if idx + 1 < len(lines):
                        next_indent = len(lines[idx + 1]) - len(lines[idx + 1].lstrip())
                        if next_indent > indent:
                            nested_obj, next_idx = self._parse_lines(lines, idx + 1, indent + 2)
                            obj[key] = nested_obj
                            idx = next_idx
                            continue

                # Regular key-value
                if value_part:
                    # Inline value
                    obj[key] = self._parse_primitive(value_part)

                idx += 1

            else:
                idx += 1

        return obj, idx

    def _parse_array_declaration(self, key_str: str) -> tuple:
        """
        Parse array declaration: key[N] or key[N]{field1,field2}

        Returns:
            (key, metadata_dict)
        """
        # Extract key
        key = key_str[:key_str.index('[')]

        # Extract length
        length_start = key_str.index('[') + 1
        length_end = key_str.index(']')
        length = int(key_str[length_start:length_end])

        meta = {'length': length, 'fields': None}

        # Check for fields
        if '{' in key_str:
            fields_start = key_str.index('{') + 1
            fields_end = key_str.index('}')
            fields_str = key_str[fields_start:fields_end]
            meta['fields'] = [f.strip() for f in fields_str.split(',')]

        return key, meta

    def _parse_csv_row(self, row_str: str) -> List[str]:
        """Parse CSV row, handling quoted strings"""
        # Simple CSV parsing (can be enhanced with proper CSV parser if needed)
        values = []
        current = ""
        in_quotes = False

        for char in row_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char

        if current:
            values.append(current.strip())

        return values

    def _parse_primitive(self, value_str: str) -> Any:
        """Parse primitive value from string"""
        value_str = value_str.strip()

        # Handle quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return json.loads(value_str)

        # Boolean
        if value_str == 'true':
            return True
        elif value_str == 'false':
            return False

        # Null
        if value_str == 'null':
            return None

        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            # String
            return value_str


def json_to_toon(json_data: Union[str, Dict, List]) -> str:
    """
    Convert JSON to TOON format.

    Args:
        json_data: JSON string or Python object

    Returns:
        TOON formatted string
    """
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    serializer = TOONSerializer()
    return serializer.serialize(data)


def toon_to_json(toon_data: str) -> str:
    """
    Convert TOON to JSON format.

    Args:
        toon_data: TOON formatted string

    Returns:
        JSON formatted string
    """
    parser = TOONParser()
    data = parser.parse(toon_data)
    return json.dumps(data, indent=2)


if __name__ == '__main__':
    # Test examples
    print("=" * 60)
    print("NexaDB TOON Format Support - Examples")
    print("=" * 60)

    # Example 1: Simple object
    print("\n[Example 1] Simple Object:")
    data1 = {
        "name": "NexaDB",
        "version": "1.0.0",
        "fast": True
    }
    toon1 = json_to_toon(data1)
    print("TOON:")
    print(toon1)

    # Example 2: Array of objects (tabular format)
    print("\n[Example 2] Tabular Array:")
    data2 = {
        "users": [
            {"id": 1, "name": "Alice", "role": "admin", "active": True},
            {"id": 2, "name": "Bob", "role": "user", "active": True},
            {"id": 3, "name": "Charlie", "role": "user", "active": False}
        ]
    }
    toon2 = json_to_toon(data2)
    print("TOON:")
    print(toon2)
    print("\nOriginal JSON size:", len(json.dumps(data2)))
    print("TOON size:", len(toon2))
    print(f"Token reduction: {((len(json.dumps(data2)) - len(toon2)) / len(json.dumps(data2)) * 100):.1f}%")

    # Example 3: Nested objects
    print("\n[Example 3] Nested Objects:")
    data3 = {
        "database": {
            "name": "NexaDB",
            "performance": {
                "writes_per_sec": 89000,
                "memory_mb": 111
            }
        }
    }
    toon3 = json_to_toon(data3)
    print("TOON:")
    print(toon3)

    # Example 4: Round-trip test
    print("\n[Example 4] Round-trip Test:")
    original = {"test": "value", "numbers": [1, 2, 3]}
    toon = json_to_toon(original)
    back_to_json = toon_to_json(toon)
    restored = json.loads(back_to_json)
    print("Original:", original)
    print("TOON:", toon)
    print("Restored:", restored)
    print("Match:", original == restored)

    print("\n" + "=" * 60)
