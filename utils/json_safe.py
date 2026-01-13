"""
Safe JSON handling utilities.
Provides defensive parsing and serialization for Discord embed storage.
"""

import json
import re
import logging
from typing import Any, Optional, TypeVar, Callable

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_json_loads(
    json_str: str,
    default: Optional[T] = None,
    validator: Optional[Callable[[Any], bool]] = None
) -> Any:
    """
    Safely parse JSON string with optional validation.
    
    Args:
        json_str: The JSON string to parse
        default: Default value if parsing fails
        validator: Optional function to validate parsed data
    
    Returns:
        Parsed JSON data or default value
    """
    if not json_str:
        return default
    
    try:
        # Clean potential markdown code blocks
        cleaned = clean_json_string(json_str)
        data = json.loads(cleaned)
        
        if validator and not validator(data):
            logger.warning("JSON validation failed")
            return default
        
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return default


def safe_json_dumps(
    data: Any,
    compact: bool = True,
    max_length: Optional[int] = None
) -> str:
    """
    Safely serialize data to JSON string.
    
    Args:
        data: Data to serialize
        compact: Whether to use compact formatting
        max_length: Optional max length for the output
    
    Returns:
        JSON string
    """
    try:
        if compact:
            result = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        else:
            result = json.dumps(data, indent=2, ensure_ascii=False)
        
        if max_length and len(result) > max_length:
            logger.warning(f"JSON output truncated from {len(result)} to {max_length}")
            # Truncate and ensure valid JSON
            result = result[:max_length - 3] + "..."
        
        return result
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        return "{}"


def clean_json_string(json_str: str) -> str:
    """
    Clean JSON string by removing markdown formatting and extra whitespace.
    """
    # Remove markdown code blocks
    json_str = re.sub(r'^```(?:json)?\s*', '', json_str.strip())
    json_str = re.sub(r'\s*```$', '', json_str.strip())
    
    # Remove leading/trailing whitespace
    json_str = json_str.strip()
    
    return json_str


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON object or array from text that may contain other content.
    """
    if not text:
        return None
    
    # Try to find JSON object
    obj_match = re.search(r'\{[\s\S]*\}', text)
    if obj_match:
        potential_json = obj_match.group()
        try:
            json.loads(potential_json)
            return potential_json
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON array
    arr_match = re.search(r'\[[\s\S]*\]', text)
    if arr_match:
        potential_json = arr_match.group()
        try:
            json.loads(potential_json)
            return potential_json
        except json.JSONDecodeError:
            pass
    
    return None


def merge_dicts(base: dict, update: dict, deep: bool = True) -> dict:
    """
    Merge two dictionaries with optional deep merge.
    """
    result = base.copy()
    
    for key, value in update.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    
    return result


def validate_state_structure(state: dict) -> tuple[bool, list[str]]:
    """
    Validate that state dictionary has required structure.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    required_keys = ["state_version", "users", "daily_flags", "bot_metadata"]
    for key in required_keys:
        if key not in state:
            errors.append(f"Missing required key: {key}")
    
    if "users" in state and not isinstance(state["users"], dict):
        errors.append("'users' must be a dictionary")
    
    if "state_version" in state and not isinstance(state["state_version"], int):
        errors.append("'state_version' must be an integer")
    
    return len(errors) == 0, errors


def truncate_for_embed(text: str, max_length: int = 4000) -> str:
    """
    Truncate text to fit in Discord embed with ellipsis.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Usage:
        safe_get(data, "user", "profile", "name", default="Unknown")
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def safe_set(data: dict, value: Any, *keys: str) -> bool:
    """
    Safely set nested dictionary value, creating intermediate dicts as needed.
    
    Returns:
        True if successful, False otherwise
    """
    if not keys:
        return False
    
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            return False
        current = current[key]
    
    current[keys[-1]] = value
    return True


def compress_for_storage(data: dict) -> str:
    """
    Compress dictionary for Discord embed storage.
    Removes None values and empty collections.
    """
    def clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items() 
                    if v is not None and v != [] and v != {}}
        elif isinstance(obj, list):
            return [clean(item) for item in obj if item is not None]
        return obj
    
    cleaned = clean(data)
    return safe_json_dumps(cleaned, compact=True)


def decompress_from_storage(json_str: str) -> dict:
    """
    Decompress JSON string from storage.
    """
    return safe_json_loads(json_str, default={})


def calculate_json_size(data: Any) -> int:
    """
    Calculate the byte size of JSON-serialized data.
    """
    json_str = safe_json_dumps(data, compact=True)
    return len(json_str.encode('utf-8'))


def fits_in_embed(data: dict, max_bytes: int = 4000) -> bool:
    """
    Check if data fits within Discord embed description limit.
    """
    return calculate_json_size(data) <= max_bytes
