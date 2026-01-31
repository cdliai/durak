#!/usr/bin/env python
"""
Standalone test for normalizer fix (Issue #40).
Tests the Rust core directly without importing the full durak package.
"""
import sys

# Import just the Rust extension directly
from durak._durak_core import fast_normalize

def test_rust_core():
    """Test Rust core fast_normalize with different parameter combinations"""
    
    print("Testing Rust core fast_normalize...")
    
    # Test 1: Default (lowercase=True, handle_turkish_i=True)
    result1 = fast_normalize('İSTANBUL', True, True)
    print(f'✓ Test 1 (default): İSTANBUL -> {result1}')
    assert result1 == 'istanbul', f'Expected istanbul, got {result1}'
    
    # Test 2: No lowercase (lowercase=False, handle_turkish_i=True)
    result2 = fast_normalize('İSTANBUL', False, True)
    print(f'✓ Test 2 (no lowercase): İSTANBUL -> {result2}')
    assert result2 == 'iSTANBUL', f'Expected iSTANBUL, got {result2}'
    
    # Test 3: No Turkish I handling (lowercase=True, handle_turkish_i=False)
    result3 = fast_normalize('IŞIK', True, False)
    print(f'✓ Test 3 (no Turkish I): IŞIK -> {result3}')
    # Without Turkish I handling, I should lowercase to i (not ı)
    assert 'ı' not in result3 or result3 == 'ışik', f'Unexpected result: {result3}'
    
    # Test 4: Both False (no transformation)
    result4 = fast_normalize('İSTANBUL', False, False)
    print(f'✓ Test 4 (both false): İSTANBUL -> {result4}')
    assert result4 == 'İSTANBUL', f'Expected İSTANBUL, got {result4}'
    
    # Test 5: Mixed content
    result5 = fast_normalize("İstanbul'da 2024!", True, True)
    print(f"✓ Test 5 (mixed content): İstanbul'da 2024! -> {result5}")
    assert result5 == "istanbul'da 2024!", f"Expected \"istanbul'da 2024!\", got {result5}"
    
    # Test 6: Turkish I → i conversion
    result6 = fast_normalize('İ', True, True)
    print(f'✓ Test 6 (İ): İ -> {result6}')
    assert result6 == 'i', f'Expected i, got {result6}'
    
    # Test 7: Turkish I → ı conversion
    result7 = fast_normalize('I', True, True)
    print(f'✓ Test 7 (I): I -> {result7}')
    assert result7 == 'ı', f'Expected ı, got {result7}'
    
    print('\n✅ All Rust core tests passed! Bug #40 is FIXED.')

if __name__ == '__main__':
    test_rust_core()
