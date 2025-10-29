"""
JSON Cache Manager for weather reasoning data

This module provides functionality to cache weather reasoning data
using JSON file storage.
"""

import json
import hashlib
import os
from typing import Optional, Dict, Any
from datetime import datetime


CACHE_FILE = "cache.json"


def generate_cache_key(lat: float, lon: float, date: str) -> str:
    """
    Generate a unique cache key from latitude, longitude, and date.

    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        date: Date string (format: YYYY-MM-DD)

    Returns:
        str: SHA256 hash of the combined parameters

    Example:
        >>> generate_cache_key(35.6762, 139.6503, "2025-01-15")
        'a1b2c3d4e5f6...'
    """
    key_string = f"{lat}_{lon}_{date}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def load_cache() -> Dict[str, Any]:
    """
    Load cache data from JSON file.

    If the file doesn't exist, returns an empty dictionary.
    If the file is corrupted, returns an empty dictionary and logs error.

    Returns:
        dict: Cache data dictionary

    Raises:
        None: All exceptions are caught and handled internally
    """
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            if not isinstance(cache_data, dict):
                print(f"Warning: Cache file is not a valid dictionary. Returning empty cache.")
                return {}
            return cache_data
    except json.JSONDecodeError as e:
        print(f"Error: Cache file is corrupted (JSONDecodeError). Details: {e}")
        print(f"Returning empty cache. Consider backing up and deleting {CACHE_FILE}")
        return {}
    except Exception as e:
        print(f"Error loading cache: {e}")
        return {}


def get_cached_reasoning(cache_key: str) -> Optional[str]:
    """
    Get cached reasoning data for a given cache key.

    Args:
        cache_key: The cache key to lookup

    Returns:
        str: The cached reasoning text if found
        None: If the key doesn't exist in cache

    Example:
        >>> key = generate_cache_key(35.6762, 139.6503, "2025-01-15")
        >>> reasoning = get_cached_reasoning(key)
        >>> print(reasoning)  # None if not cached, or the reasoning text
    """
    cache_data = load_cache()

    if cache_key not in cache_data:
        return None

    entry = cache_data[cache_key]
    if isinstance(entry, dict) and "reasoning" in entry:
        return entry["reasoning"]

    return None


def save_to_cache(cache_key: str, reasoning: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save reasoning data to cache with optional metadata.

    Args:
        cache_key: The cache key to store under
        reasoning: The reasoning text to cache
        metadata: Optional dictionary of metadata to store alongside reasoning

    Returns:
        bool: True if save was successful, False otherwise

    Example:
        >>> key = generate_cache_key(35.6762, 139.6503, "2025-01-15")
        >>> metadata = {"temperature": 25, "humidity": 60}
        >>> save_to_cache(key, "Weather looks good", metadata)
        True
    """
    try:
        # Load existing cache
        cache_data = load_cache()

        # Prepare cache entry
        cache_entry = {
            "reasoning": reasoning,
            "cached_at": datetime.now().isoformat(),
        }

        # Add metadata if provided
        if metadata is not None:
            cache_entry["metadata"] = metadata

        # Update cache
        cache_data[cache_key] = cache_entry

        # Save to file
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"Error saving to cache: {e}")
        return False


# Export all public functions
__all__ = [
    'generate_cache_key',
    'load_cache',
    'get_cached_reasoning',
    'save_to_cache',
    'CACHE_FILE'
]
