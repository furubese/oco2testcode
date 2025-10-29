"""
Test script for cache_manager.py
Tests all required functionality including error handling
"""

import os
import sys
import json

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from cache_manager import (
    generate_cache_key,
    load_cache,
    get_cached_reasoning,
    save_to_cache,
    CACHE_FILE
)


def cleanup_cache():
    """Remove cache file if it exists"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(f"✓ Cleaned up {CACHE_FILE}")


def test_generate_cache_key():
    """Test 4: Cache key generation"""
    print("\n=== Test 4: Cache Key Generation ===")
    key1 = generate_cache_key(35.6762, 139.6503, "2025-01-15")
    key2 = generate_cache_key(35.6762, 139.6503, "2025-01-15")
    key3 = generate_cache_key(35.6762, 139.6503, "2025-01-16")

    print(f"Key 1: {key1[:16]}...")
    print(f"Key 2: {key2[:16]}...")
    print(f"Key 3: {key3[:16]}...")

    assert key1 == key2, "Same parameters should generate same key"
    assert key1 != key3, "Different parameters should generate different key"
    assert len(key1) == 64, "SHA256 should be 64 characters"
    print("✓ Cache key generation works correctly")


def test_cache_save_and_load():
    """Test 5 & 6: Save data and verify cache.json is created and data can be loaded"""
    print("\n=== Test 5: Cache Save (cache.json creation) ===")

    # Clean up first
    cleanup_cache()

    # Generate test data
    test_key = generate_cache_key(35.6762, 139.6503, "2025-01-15")
    test_reasoning = "The weather is sunny with a high of 25°C"
    test_metadata = {
        "temperature": 25,
        "humidity": 60,
        "location": "Tokyo"
    }

    # Save to cache
    result = save_to_cache(test_key, test_reasoning, test_metadata)
    assert result == True, "save_to_cache should return True"
    print("✓ save_to_cache returned True")

    # Verify file exists
    assert os.path.exists(CACHE_FILE), f"{CACHE_FILE} should be created"
    print(f"✓ {CACHE_FILE} was created")

    # Verify file content
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert test_key in data, "Cache key should exist in file"
        assert data[test_key]["reasoning"] == test_reasoning, "Reasoning should match"
        assert data[test_key]["metadata"] == test_metadata, "Metadata should match"
        assert "cached_at" in data[test_key], "cached_at timestamp should exist"
    print("✓ Cache file contains correct data")

    print("\n=== Test 6: Cache Load (data retrieval) ===")

    # Test get_cached_reasoning
    retrieved_reasoning = get_cached_reasoning(test_key)
    assert retrieved_reasoning == test_reasoning, "Retrieved reasoning should match"
    print(f"✓ Retrieved reasoning: '{retrieved_reasoning[:50]}...'")

    # Test load_cache
    cache_data = load_cache()
    assert isinstance(cache_data, dict), "load_cache should return dict"
    assert test_key in cache_data, "Cache should contain our key"
    print("✓ load_cache works correctly")


def test_nonexistent_key():
    """Test 7: Non-existent key returns None"""
    print("\n=== Test 7: Non-existent Key Returns None ===")

    fake_key = "nonexistent_key_12345"
    result = get_cached_reasoning(fake_key)

    assert result is None, "Non-existent key should return None"
    print(f"✓ get_cached_reasoning('{fake_key}') returned None")


def test_corrupted_json():
    """Test 8: Corrupted JSON error handling"""
    print("\n=== Test 8: Corrupted JSON Error Handling ===")

    # Create corrupted JSON file
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        f.write("{ invalid json content here }")
    print("✓ Created corrupted JSON file")

    # Test load_cache with corrupted file
    cache_data = load_cache()
    assert cache_data == {}, "Corrupted file should return empty dict"
    print("✓ load_cache handled corrupted JSON and returned empty dict")

    # Test get_cached_reasoning with corrupted file
    result = get_cached_reasoning("any_key")
    assert result is None, "Should return None with corrupted cache"
    print("✓ get_cached_reasoning returned None with corrupted cache")

    # Verify we can recover by saving new data
    test_key = generate_cache_key(1.0, 2.0, "2025-01-01")
    success = save_to_cache(test_key, "Recovery test", {"status": "recovered"})
    assert success == True, "Should be able to save after corruption"
    print("✓ Cache recovered successfully after corruption")

    # Verify recovery
    retrieved = get_cached_reasoning(test_key)
    assert retrieved == "Recovery test", "Should retrieve data after recovery"
    print("✓ Data retrieval works after recovery")


def test_multiple_entries():
    """Additional test: Multiple cache entries"""
    print("\n=== Additional Test: Multiple Cache Entries ===")

    cleanup_cache()

    # Save multiple entries
    entries = [
        (35.6762, 139.6503, "2025-01-15", "Tokyo weather"),
        (34.0522, -118.2437, "2025-01-15", "LA weather"),
        (51.5074, -0.1278, "2025-01-15", "London weather"),
    ]

    for lat, lon, date, reasoning in entries:
        key = generate_cache_key(lat, lon, date)
        save_to_cache(key, reasoning, {"lat": lat, "lon": lon})

    print(f"✓ Saved {len(entries)} cache entries")

    # Verify all entries exist
    for lat, lon, date, expected_reasoning in entries:
        key = generate_cache_key(lat, lon, date)
        reasoning = get_cached_reasoning(key)
        assert reasoning == expected_reasoning, f"Mismatch for {lat}, {lon}"

    print("✓ All entries retrieved correctly")

    # Check cache file structure
    cache_data = load_cache()
    assert len(cache_data) == len(entries), "Cache should have all entries"
    print(f"✓ Cache contains {len(cache_data)} entries")


def main():
    """Run all tests"""
    print("=" * 60)
    print("CACHE MANAGER TEST SUITE")
    print("=" * 60)

    try:
        test_generate_cache_key()
        test_cache_save_and_load()
        test_nonexistent_key()
        test_corrupted_json()
        test_multiple_entries()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)

        # Final cleanup
        cleanup_cache()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
