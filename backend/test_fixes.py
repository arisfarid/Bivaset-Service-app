#!/usr/bin/env python3
"""
Test script to verify that the key fixes work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from localization import get_message
from keyboards import get_employer_menu_keyboard, get_main_menu_keyboard

def test_localization():
    """Test the localization function with None context"""
    print("Testing localization with None context...")
    
    # Create a mock context object
    mock_context = type('obj', (object,), {'user_data': {'lang': 'fa', 'name': 'کاربر'}})
    
    try:
        # Test basic message
        message = get_message("welcome", mock_context)
        print(f"✓ Basic message test passed: {message[:50]}...")
        
        # Test message with category_name parameter
        message = get_message("subcategory_selection", mock_context, category_name="تست")
        print(f"✓ Category name parameter test passed: {message[:50]}...")
        
        # Test with None context
        message = get_message("welcome", None)
        print(f"✓ None context test passed: {message[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Localization test failed: {e}")
        return False

def test_keyboards():
    """Test keyboard functions with optional context"""
    print("\nTesting keyboard functions...")
    
    # Create a mock context object
    mock_context = type('obj', (object,), {'user_data': {'lang': 'fa', 'name': 'کاربر'}})
    
    try:
        # Test employer menu keyboard with context
        keyboard = get_employer_menu_keyboard(mock_context)
        print(f"✓ Employer menu with context: {len(keyboard.inline_keyboard)} rows")
        
        # Test employer menu keyboard without context (should not fail)
        keyboard = get_employer_menu_keyboard()
        print(f"✓ Employer menu without context: {len(keyboard.inline_keyboard)} rows")
        
        # Test main menu keyboard with context
        keyboard = get_main_menu_keyboard(mock_context)
        print(f"✓ Main menu with context: {len(keyboard.inline_keyboard)} rows")
        
        # Test main menu keyboard without context
        keyboard = get_main_menu_keyboard()
        print(f"✓ Main menu without context: {len(keyboard.inline_keyboard)} rows")
        
        return True
    except Exception as e:
        print(f"✗ Keyboard test failed: {e}")
        return False

def test_phone_decorator():
    """Test that phone decorator imports correctly"""
    print("\nTesting phone decorator import...")
    
    try:
        from handlers.phone_handler import require_phone
        print("✓ Phone decorator imported successfully")
        return True
    except Exception as e:
        print(f"✗ Phone decorator import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Running Telegram Bot Fix Tests ===\n")
    
    tests = [
        test_localization,
        test_keyboards,
        test_phone_decorator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The fixes should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
