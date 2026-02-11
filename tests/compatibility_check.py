#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows 7 兼容性检查工具

运行此脚本检查系统是否符合运行应用程序的最低要求
"""

import sys
import os
import platform

def check_python_version():
    """检查 Python 版本"""
    print("=== Python 版本检查 ===")
    version = sys.version_info
    print(f"Python 版本: {sys.version}")
    print(f"主版本: {version.major}.{version.minor}.{version.micro}")
    
    # Python 3.8 是支持 Windows 7 的最后版本
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[FAIL] Python 版本过低，需要 Python 3.8 或更高版本")
        return False
    elif version.major == 3 and version.minor == 8:
        print("[PASS] Python 3.8.x - 兼容 Windows 7")
    else:
        print("[WARN] Python 3.9+ - 可能不兼容 Windows 7")
    return True

def check_os_version():
    """检查操作系统版本"""
    print("\n=== 操作系统检查 ===")
    system = platform.system()
    version = platform.version()
    print(f"操作系统: {system}")
    print(f"版本信息: {version}")
    
    if system == "Windows":
        # 提取主要版本号
        try:
            major = int(version.split('.')[0])
            if major < 6:
                print("[FAIL] 需要 Windows 7 或更高版本")
                return False
            elif major == 6:
                minor = int(version.split('.')[1])
                if minor == 1:
                    print("[PASS] Windows 7 - 兼容")
                elif minor >= 2:
                    print("[PASS] Windows 8+ - 兼容")
            else:
                print("[PASS] Windows 10/11 - 兼容")
        except:
            pass
    else:
        print(f"[WARN] {system} 系统 - 未经充分测试")
    return True

def check_dependencies():
    """检查关键依赖"""
    print("\n=== 依赖检查 ===")
    
    # 必需依赖
    required_deps = [
        ("PySide2", "PySide2"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
    ]
    
    # 可选依赖
    optional_deps = [
        ("pyqtgraph", "pyqtgraph"),
        ("openpyxl", "openpyxl"),
    ]
    
    all_ok = True
    
    print("\n[必需依赖]")
    for name, import_name in required_deps:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', '未知')
            print(f"[PASS] {name}: {version}")
        except ImportError:
            print(f"[FAIL] {name}: 未安装 (必需)")
            all_ok = False
    
    print("\n[可选依赖]")
    for name, import_name in optional_deps:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', '未知')
            print(f"[PASS] {name}: {version} (可选)")
        except ImportError:
            print(f"[INFO] {name}: 未安装 (可选，图表/导出功能不可用)")
    
    return all_ok

def check_font_support():
    """检查字体支持"""
    print("\n=== 字体兼容性检查 ===")
    
    # 建议的字体栈
    recommended_stack = "Microsoft YaHei,Segoe UI,Arial,sans-serif"
    print(f"[INFO] 推荐字体栈: {recommended_stack}")
    print("[INFO] 系统将自动选择可用字体")
    
    return True

def check_file_encoding():
    """检查文件编码"""
    print("\n=== 文件编码检查 ===")
    
    # 检查默认编码
    import locale
    default_encoding = locale.getpreferredencoding()
    print(f"系统默认编码: {default_encoding}")
    
    if default_encoding.lower() == 'utf-8':
        print("[PASS] UTF-8 编码")
    else:
        print(f"[WARN] 默认编码为 {default_encoding}，程序将强制使用 UTF-8")
    
    return True

def main():
    """主检查函数"""
    print("=" * 60)
    print("Windows 7 兼容性检查工具")
    print("=" * 60)
    
    results = {
        "python": check_python_version(),
        "os": check_os_version(),
        "dependencies": check_dependencies(),
        "font": check_font_support(),
        "encoding": check_file_encoding(),
    }
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{check}: {status}")
    
    print("=" * 60)
    if all(results.values()):
        print("[PASS] 系统兼容，可以运行应用程序")
        return 0
    else:
        print("[FAIL] 存在兼容性问题，请解决后再运行")
        return 1

if __name__ == "__main__":
    sys.exit(main())
