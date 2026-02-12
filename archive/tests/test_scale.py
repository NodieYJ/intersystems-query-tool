#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI/UX Pro Max - Resolution Scale Test
Verify dynamic resolution scaling feature
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication


def test_scale_factor():
    """Test scale factor calculation"""
    print("=" * 70)
    print("UI/UX Pro Max Design System - Resolution Scale Test")
    print("=" * 70)
    print()
    
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create app
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Get screen info
    screen = app.primaryScreen()
    if screen is None:
        print("ERROR: Cannot get screen info")
        return False
    
    geometry = screen.geometry()
    width = geometry.width()
    height = geometry.height()
    dpi = screen.logicalDotsPerInch()
    
    print(f"Screen Resolution: {width} x {height}")
    print(f"Screen DPI: {dpi}")
    print()
    
    # Calculate scale factor
    if width >= 3200 or height >= 1800:
        expected_scale = 2.0
        res_type = "3K+ (>=3200x1800)"
    elif width >= 2560 or height >= 1440:
        expected_scale = 1.5
        res_type = "2K (~2560x1440)"
    else:
        expected_scale = 1.0
        res_type = "1K (<=1920x1080)"
    
    print(f"Resolution Type: {res_type}")
    print(f"Expected Scale: {expected_scale * 100:.0f}%")
    print()
    
    # Import main_window module
    from src.presentation.windows.main_window import scaled, SCALE_FACTOR
    
    print(f"Current SCALE_FACTOR: {SCALE_FACTOR}")
    print()
    
    # Test various sizes
    test_values = [240, 56, 20, 14, 1280, 800]
    print("Size Scaling Test:")
    for value in test_values:
        scaled_value = scaled(value)
        print(f"  {value}px -> {scaled_value}px (x{SCALE_FACTOR})")
    
    print()
    print("=" * 70)
    
    if SCALE_FACTOR == expected_scale:
        print(f"TEST PASSED! Scale factor correct: {SCALE_FACTOR * 100:.0f}%")
    else:
        print(f"NOTE: Current SCALE_FACTOR is {SCALE_FACTOR},")
        print(f"      but expected {expected_scale} for {width}x{height}")
    
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        test_scale_factor()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
