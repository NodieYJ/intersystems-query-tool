#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖检查脚本

检查所有必需和可选依赖是否已安装
"""

import sys
import importlib
from typing import Dict, Tuple


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    检查包是否可用
    
    Args:
        package_name: 包名称
        import_name: 导入名称（默认与包名称相同）
        
    Returns:
        Tuple[bool, str]: (是否可用, 消息)
    """
    try:
        importlib.import_module(import_name or package_name)
        return True, f"[OK] {package_name}"
    except ImportError:
        return False, f"[MISSING] {package_name}"


def check_optional_package(package_name: str, description: str = "") -> Tuple[bool, str]:
    """
    检查可选包是否可用
    
    Args:
        package_name: 包名称
        description: 功能描述
        
    Returns:
        Tuple[bool, str]: (是否可用, 消息)
    """
    try:
        importlib.import_module(package_name)
        msg = f"[OK] {package_name}"
        if description:
            msg += f" ({description})"
        return True, msg
    except ImportError:
        msg = f"[OPTIONAL] {package_name}"
        if description:
            msg += f" ({description})"
        return False, msg


def main():
    """主函数"""
    print("=" * 60)
    print("PyWindows 依赖检查")
    print("=" * 60)
    
    all_required_ok = True
    
    print("\n必需依赖:")
    print("-" * 40)
    
    # 必需依赖
    required = [
        ("PySide2", "PySide2", "GUI框架"),
        ("cryptography", "cryptography", "密码加密"),
        ("requests", "requests", "HTTP请求"),
    ]
    
    for package, import_name, description in required:
        ok, msg = check_package(package, import_name)
        print(f"  {msg}")
        if not ok:
            all_required_ok = False
            print(f"     -> 请安装: pip install {package}")
    
    print("\n可选依赖 (数据库驱动):")
    print("-" * 40)
    
    # 可选依赖
    optional = [
        ("intersystems_irispython", "Intersystems IRIS", "IRIS数据库"),
        ("pymysql", "MySQL", "MySQL数据库"),
        ("psycopg2", "PostgreSQL", "PostgreSQL数据库"),
        ("pyodbc", "SQL Server", "SQL Server数据库"),
        ("cx_Oracle", "Oracle", "Oracle数据库"),
    ]
    
    for package, name, description in optional:
        ok, msg = check_optional_package(package, description)
        print(f"  {msg}")
    
    print("\n开发依赖:")
    print("-" * 40)
    
    dev = [
        ("pytest", "pytest", "测试框架"),
        ("flake8", "flake8", "代码检查"),
        ("black", "black", "代码格式化"),
        ("isort", "isort", "导入排序"),
    ]
    
    for package, name, description in dev:
        ok, msg = check_optional_package(package, description)
        print(f"  {msg}")
    
    print("\n" + "=" * 60)
    
    if all_required_ok:
        print("[OK] 所有必需依赖已安装！")
        return 0
    else:
        print("[ERROR] 缺少必需依赖！")
        print("\n安装所有必需依赖:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
