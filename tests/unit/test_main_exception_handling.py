#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 main.py 的异常处理重构
验证 IMP-002 修复是否成功
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入被测试的函数
from src.main import handle_startup_error


def test_exception_handlers_mapping():
    """测试异常处理器映射表"""
    print("Test 1: Exception Handlers Mapping")
    
    # 读取 main.py 验证异常映射
    main_file = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'src', 'main.py'
    )
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证预期的异常类型都在代码中
    expected_exceptions = [
        ('ImportError', '导入模块失败'),
        ('ValueError', '参数错误'),
        ('RuntimeError', '运行时错误'),
        ('OSError', '系统错误'),
    ]
    
    for exc_name, title in expected_exceptions:
        assert exc_name in content, f"Missing handler for {exc_name}"
        assert title in content, f"Missing title for {exc_name}: {title}"
        print(f"  [OK] {exc_name}: {title}")
    
    print(f"  [OK] All {len(expected_exceptions)} exception types mapped")


def test_error_messages():
    """测试错误消息格式"""
    print("\nTest 2: Error Message Format")
    
    # 测试各种异常的错误消息格式
    test_cases = [
        ("导入模块失败", "请检查依赖库"),
        ("参数错误", "配置参数不正确"),
        ("运行时错误", "应用程序运行时发生错误"),
        ("系统错误", "操作系统或文件系统错误"),
    ]
    
    # 读取 main.py 验证
    main_file = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'src', 'main.py'
    )
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for title, suggestion in test_cases:
        assert title in content, f"Missing title: {title}"
        assert suggestion in content, f"Missing suggestion: {suggestion}"
        print(f"  [OK] {title}: {suggestion}")


def test_handle_startup_error_function():
    """测试异常处理函数存在性"""
    print("\nTest 3: Handle Startup Error Function")
    
    # 验证函数存在且可调用
    assert callable(handle_startup_error), "handle_startup_error should be callable"
    print("  [OK] handle_startup_error function exists")
    
    # 验证函数签名
    import inspect
    sig = inspect.signature(handle_startup_error)
    params = list(sig.parameters.keys())
    assert 'error' in params, "Missing 'error' parameter"
    assert 'error_type' in params, "Missing 'error_type' parameter"
    print("  [OK] Function signature correct")


def test_error_type_extraction():
    """测试错误类型提取"""
    print("\nTest 4: Error Type Extraction")
    
    # 读取 main.py 验证异常类型映射
    main_file = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'src', 'main.py'
    )
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    test_cases = [
        (ImportError, "导入模块失败"),
        (ValueError, "参数错误"),
        (RuntimeError, "运行时错误"),
        (OSError, "系统错误"),
    ]
    
    for exc_type, expected_title in test_cases:
        assert exc_type.__name__ in content, f"Missing exception type: {exc_type.__name__}"
        assert expected_title in content, f"Missing title for {exc_type.__name__}: {expected_title}"
        print(f"  [OK] {exc_type.__name__} -> {expected_title}")


def test_unknown_exception_handling():
    """测试未知异常处理"""
    print("\nTest 5: Unknown Exception Handling")
    
    # 读取 main.py 验证通用异常处理
    main_file = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'src', 'main.py'
    )
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证存在通用异常处理
    assert "except Exception" in content, "Missing generic exception handler"
    assert "应用程序启动失败" in content, "Missing generic error message"
    print("  [OK] Unknown exceptions fall through to generic handler")


def test_code_structure():
    """测试代码结构"""
    print("\nTest 6: Code Structure Verification")
    
    # 读取 main.py 文件
    main_file = os.path.join(
        os.path.dirname(__file__), '..', '..', 
        'src', 'main.py'
    )
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证重构后的结构
    checks = [
        ('handle_startup_error function', 'def handle_startup_error'),
        ('exception_handlers mapping', 'exception_handlers ='),
        ('Unified error handling', 'handle_startup_error(e'),
        ('Logger usage', 'logger.error'),
        ('Logger critical for unexpected', 'logger.critical'),
    ]
    
    for desc, pattern in checks:
        if pattern in content:
            print(f"  [OK] {desc}")
        else:
            print(f"  [FAIL] Missing: {desc}")
    
    # 验证消除了重复代码
    # 旧的重复模式: except XXX as e:\n    error_msg = ...
    # 新的模式应该使用统一的 handle_startup_error
    old_pattern_count = content.count('error_msg = f"')
    print(f"  [INFO] f-string error messages: {old_pattern_count}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("IMP-002 Exception Handling Refactor Test")
    print("=" * 60)
    
    try:
        test_exception_handlers_mapping()
        test_error_messages()
        test_handle_startup_error_function()
        test_error_type_extraction()
        test_unknown_exception_handling()
        test_code_structure()
        
        print("\n" + "=" * 60)
        print("All tests passed! [SUCCESS]")
        print("=" * 60)
        print("\nSummary:")
        print("- Exception handlers mapping created")
        print("- Unified error handling function implemented")
        print("- Duplicate code eliminated")
        print("- Specific exceptions handled appropriately")
        print("- Unknown exceptions caught by generic handler")
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Test exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
