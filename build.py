#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
构建脚本
用于本地构建和测试
"""

import os
import subprocess
import sys
import shutil


def run_command(command, cwd=None):
    """
    运行命令

    Args:
        command: 命令字符串
        cwd: 工作目录

    Returns:
        tuple: (返回码, 输出, 错误)
    """
    print(f"执行命令: {command}")
    result = subprocess.run(
        command, 
        shell=True, 
        capture_output=True, 
        text=True, 
        cwd=cwd
    )
    print(f"返回码: {result.returncode}")
    if result.stdout:
        print(f"输出: {result.stdout}")
    if result.stderr:
        print(f"错误: {result.stderr}")
    return result.returncode, result.stdout, result.stderr


def lint_check():
    """
    代码风格检查
    """
    print("\n=== 代码风格检查 ===")
    
    # 检查是否安装了必要的工具
    tools = ["flake8", "black", "isort"]
    for tool in tools:
        code, _, _ = run_command(f"python -m pip show {tool}")
        if code != 0:
            print(f"安装 {tool}...")
            run_command(f"python -m pip install {tool}")
    
    # 运行flake8
    print("\n运行 flake8...")
    code, _, _ = run_command("python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics")
    if code != 0:
        print("flake8 检查失败")
        return False
    
    # 运行black检查
    print("\n运行 black 检查...")
    code, _, _ = run_command("python -m black --check .")
    if code != 0:
        print("black 检查失败")
        return False
    
    # 运行isort检查
    print("\n运行 isort 检查...")
    code, _, _ = run_command("python -m isort --check-only .")
    if code != 0:
        print("isort 检查失败")
        return False
    
    print("代码风格检查通过")
    return True


def run_tests():
    """
    运行单元测试
    """
    print("\n=== 运行单元测试 ===")
    
    # 检查是否安装了pytest
    code, _, _ = run_command("python -m pip show pytest")
    if code != 0:
        print("安装 pytest...")
        run_command("python -m pip install pytest")
    
    # 运行测试
    code, _, _ = run_command("python -m unittest discover tests/unit")
    if code != 0:
        print("单元测试失败")
        return False
    
    print("单元测试通过")
    return True


def build_app():
    """
    构建应用程序
    """
    print("\n=== 构建应用程序 ===")
    
    # 检查是否安装了pyinstaller
    code, _, _ = run_command("python -m pip show pyinstaller")
    if code != 0:
        print("安装 pyinstaller...")
        run_command("python -m pip install pyinstaller")
    
    # 清理之前的构建
    if os.path.exists("dist"):
        print("清理之前的构建...")
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # 构建应用
    print("构建应用...")
    code, _, _ = run_command(
        "python -m pyinstaller --onefile --windowed --name desktop_app src/main.py"
    )
    if code != 0:
        print("构建失败")
        return False
    
    print("构建成功")
    return True


def main():
    """
    主函数
    """
    print("=== 构建脚本 ===")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 安装依赖
    print("\n=== 安装依赖 ===")
    if os.path.exists("requirements.txt"):
        print("安装项目依赖...")
        run_command("python -m pip install -r requirements.txt")
    
    # 运行检查和构建
    success = True
    
    # 代码风格检查
    if not lint_check():
        success = False
    
    # 运行测试
    if not run_tests():
        success = False
    
    # 构建应用
    if success:
        if not build_app():
            success = False
    
    if success:
        print("\n=== 构建流程完成 ===")
        print("所有检查和构建都成功完成！")
        return 0
    else:
        print("\n=== 构建流程失败 ===")
        print("构建流程中出现错误，请检查输出信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
