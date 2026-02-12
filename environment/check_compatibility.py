#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python 3.8 兼容性检查脚本

根据 SYSTEM_REQUIREMENTS.md 和 diffenvironment.md 验证项目兼容性
"""

import sys
import os
import re
import ast

def check_python_version():
    """检查 Python 版本"""
    print("=" * 60)
    print("1. Python 版本检查")
    print("=" * 60)
    
    REQUIRED_MAJOR = 3
    REQUIRED_MINOR = 8
    REQUIRED_MICRO = 10
    
    version_info = sys.version_info
    
    if version_info.major != REQUIRED_MAJOR or version_info.minor != REQUIRED_MINOR:
        print(f"❌ 错误: 需要 Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.x")
        print(f"   当前: {version_info.major}.{version_info.minor}.{version_info.micro}")
        return False
    
    if version_info.micro > REQUIRED_MICRO:
        print(f"⚠️  警告: 建议使用 Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.{REQUIRED_MICRO}")
        print(f"   当前: {version_info.major}.{version_info.minor}.{version_info.micro}")
    else:
        print(f"✅ Python 版本正确: {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    return True

def check_file_syntax(filepath):
    """检查单个文件的语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用 AST 解析检查语法
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def check_builtin_generics(filepath, content):
    """检查内置泛型类型注解 (Python 3.9+ 语法)"""
    issues = []
    
    # 匹配内置泛型类型注解，如: tuple[int, int], list[str], dict[str, int]
    patterns = [
        (r':\s*list\[[^\]]+\]', 'list[...]'),
        (r':\s*dict\[[^\]]+\]', 'dict[...]'),
        (r':\s*tuple\[[^\]]+\]', 'tuple[...]'),
        (r':\s*set\[[^\]]+\]', 'set[...]'),
    ]
    
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern, type_name in patterns:
            if re.search(pattern, line):
                # 排除注释行和字符串
                stripped = line.strip()
                if not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    issues.append((filepath, line_num, line.strip(), type_name))
    
    return issues

def check_union_syntax(filepath, content):
    """检查联合类型语法 (Python 3.10+ 语法)"""
    issues = []
    
    # 匹配 X | Y 联合类型语法
    pattern = r':\s*\w+\s*\|\s*(None|\w+)'
    
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        if re.search(pattern, line):
            stripped = line.strip()
            if not stripped.startswith('#'):
                issues.append((filepath, line_num, line.strip(), 'X | Y'))
    
    return issues

def check_all_python_files():
    """检查所有 Python 文件"""
    print("\n" + "=" * 60)
    print("2. Python 文件语法检查")
    print("=" * 60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, '..', 'src')
    
    all_ok = True
    total_files = 0
    builtin_generic_issues = []
    union_syntax_issues = []
    
    for root, dirs, files in os.walk(src_dir):
        # 排除 __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                total_files += 1
                
                # 检查语法
                ok, error = check_file_syntax(filepath)
                if not ok:
                    print(f"❌ 语法错误: {filepath}")
                    print(f"   错误: {error}")
                    all_ok = False
                    continue
                
                # 读取内容检查类型注解
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    builtin_generic_issues.extend(check_builtin_generics(filepath, content))
                    union_syntax_issues.extend(check_union_syntax(filepath, content))
                except Exception as e:
                    print(f"⚠️  无法读取文件: {filepath} - {e}")
    
    print(f"✅ 已检查 {total_files} 个 Python 文件")
    
    # 报告内置泛型问题
    if builtin_generic_issues:
        print(f"\n❌ 发现 {len(builtin_generic_issues)} 处 Python 3.9+ 内置泛型语法:")
        for filepath, line_num, line, type_name in builtin_generic_issues[:5]:
            rel_path = os.path.relpath(filepath, project_root)
            print(f"   {rel_path}:{line_num}: {type_name}")
            print(f"      {line[:80]}")
        if len(builtin_generic_issues) > 5:
            print(f"   ... 还有 {len(builtin_generic_issues) - 5} 处")
        all_ok = False
    else:
        print("✅ 未发现 Python 3.9+ 内置泛型语法问题")
    
    # 报告联合类型问题
    if union_syntax_issues:
        print(f"\n❌ 发现 {len(union_syntax_issues)} 处 Python 3.10+ 联合类型语法:")
        for filepath, line_num, line, type_name in union_syntax_issues[:5]:
            rel_path = os.path.relpath(filepath, project_root)
            print(f"   {rel_path}:{line_num}: {type_name}")
            print(f"      {line[:80]}")
        all_ok = False
    else:
        print("✅ 未发现 Python 3.10+ 联合类型语法问题")
    
    return all_ok

def check_setup_py():
    """检查 setup.py 配置"""
    print("\n" + "=" * 60)
    print("3. setup.py 配置检查")
    print("=" * 60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    setup_path = os.path.join(project_root, '..', 'setup.py')
    
    try:
        with open(setup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 python_requires
        if 'python_requires=' in content or 'python_requires =' in content:
            if '>=3.8' in content and '<3.9' in content:
                print("✅ setup.py 已配置 python_requires='>=3.8,<3.9'")
                return True
            else:
                print("⚠️  setup.py 有 python_requires 但版本范围可能不正确")
                return False
        else:
            print("❌ setup.py 缺少 python_requires 配置")
            return False
    except Exception as e:
        print(f"❌ 无法读取 setup.py: {e}")
        return False

def check_pyproject_toml():
    """检查 pyproject.toml 配置"""
    print("\n" + "=" * 60)
    print("4. pyproject.toml 配置检查")
    print("=" * 60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    toml_path = os.path.join(project_root, '..', 'pyproject.toml')
    
    try:
        with open(toml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        
        # 检查 requires-python
        if 'requires-python' in content and '>=3.8' in content:
            checks.append(("requires-python", True))
        else:
            checks.append(("requires-python", False))
        
        # 检查 black 配置
        if '[tool.black]' in content and "target-version = ['py38']" in content:
            checks.append(("black target-version", True))
        else:
            checks.append(("black target-version", False))
        
        all_ok = all(c[1] for c in checks)
        
        for name, ok in checks:
            status = "✅" if ok else "❌"
            print(f"{status} {name}")
        
        return all_ok
    except Exception as e:
        print(f"❌ 无法读取 pyproject.toml: {e}")
        return False

def main():
    """主函数"""
    print("Python 3.8 兼容性检查")
    print(f"检查时间: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}")
    
    results = []
    
    # 1. Python 版本
    results.append(("Python 版本", check_python_version()))
    
    # 2. 文件语法
    results.append(("Python 文件语法", check_all_python_files()))
    
    # 3. setup.py
    results.append(("setup.py 配置", check_setup_py()))
    
    # 4. pyproject.toml
    results.append(("pyproject.toml 配置", check_pyproject_toml()))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！项目符合 Python 3.8.10 兼容性要求")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分检查失败，请查看上方详细信息")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
