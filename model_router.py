#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能模型切换器
根据任务类型自动选择最优模型
"""

import sys
import subprocess

# 可用的模型列表 (仅免费模型)
AVAILABLE_MODELS = {
    # ===== GLM 免费模型 =====
    'glm-4.7-free': 'glm-4.7-free',
    'glm-4-flash': 'glm-4-flash',
    'glm-4': 'glm-4',
    'glm-4-plus': 'glm-4-plus',
    
    # ===== NVIDIA NIM 免费模型 (需要 NGC API Key) =====
    # Meta Llama 3 系列 (免费试用)
    'nim-llama3-8b': 'meta/llama3-8b-instruct',
    'nim-llama3-70b': 'meta/llama3-70b-instruct',
    
    # Meta Llama 3.1 系列
    'nim-llama3.1-8b': 'meta/llama3.1-8b-instruct',
    'nim-llama3.1-70b': 'meta/llama3.1-70b-instruct',
    
    # Meta Llama 3.2 (最新轻量级)
    'nim-llama3.2-1b': 'meta/llama3.2-1b-instruct',
    'nim-llama3.2-3b': 'meta/llama3.2-3b-instruct',
    
    # DeepSeek R1 系列 (免费试用)
    'nim-deepseek-r1': 'deepseek-ai/deepseek-r1',
    'nim-deepseek-r1-llama-8b': 'deepseek-ai/deepseek-r1-distill-llama-8b',
    
    # Google Gemma 2 (免费试用)
    'nim-gemma2-2b': 'google/gemma-2-2b-it',
    'nim-gemma2-9b': 'google/gemma-2-9b-it',
    
    # Qwen2 系列 (免费试用)
    'nim-qwen2-1.5b': 'qwen/qwen2-1.5b-instruct',
    'nim-qwen2-7b': 'qwen/qwen2-7b-instruct',
}

# 任务-模型映射表
TASK_MODEL_MAP = {
    # 代码任务 -> Llama3-70B
    'code': 'nim-llama3-70b',
    'coding': 'nim-llama3-70b',
    'programming': 'nim-llama3-70b',
    'debug': 'nim-llama3-70b',
    'refactor': 'nim-llama3-70b',
    'sql': 'nim-llama3-70b',
    'algorithm': 'nim-llama3-70b',
    '架构': 'nim-llama3-70b',
    '重构': 'nim-llama3-70b',
    '代码': 'nim-llama3-70b',
    '优化': 'nim-llama3-70b',
    
    # 代码/分析 -> DeepSeek R1
    'analysis': 'nim-deepseek-r1',
    'reasoning': 'nim-deepseek-r1',
    '分析': 'deepseek-r1',
    
    # 小型代码任务 -> Llama3-8B (更快)
    'quick_code': 'nim-llama3-8b',
    '简单代码': 'nim-llama3-8b',
    
    # 文档/中文任务 -> GLM
    'doc': 'glm-4.7-free',
    'document': 'glm-4.7-free',
    'write': 'glm-4.7-free',
    'readme': 'glm-4.7-free',
    'explain': 'glm-4.7-free',
    '文档': 'glm-4.7-free',
    '说明': 'glm-4.7-free',
    '介绍': 'glm-4.7-free',
    '总结': 'glm-4.7-free',
    
    # 快速任务 -> GLM
    'quick': 'glm-4.7-free',
    'check': 'glm-4.7-free',
    '查看': 'glm-4.7-free',
    '检查': 'glm-4.7-free',
}

# 代码相关关键词
code_keywords = [
    'def ', 'class ', 'import ', 'function', 'method',
    'python', 'py', 'sql', 'query', 'database',
    'refactor', 'optimize', 'performance', 'memory',
    '架构', '重构', '优化', '拆分'
]

def detect_task_type(user_input):
    """检测任务类型"""
    user_input_lower = user_input.lower()
    
    # 检查代码关键词
    for keyword in code_keywords:
        if keyword in user_input_lower:
            return 'nim-llama3-70b', f'检测到代码关键词: {keyword}'
    
    # 检查任务映射
    for task, model in TASK_MODEL_MAP.items():
        if task in user_input_lower:
            return model, f'匹配任务类型: {task}'
    
    # 默认使用 GLM
    return 'glm-4.7-free', '默认使用通用模型'

def list_available_models():
    """显示所有可用模型"""
    print("\n" + "="*60)
    print("可用模型列表 (免费)")
    print("="*60)
    
    print("\n[GLM 模型]")
    print("-" * 40)
    for k, v in AVAILABLE_MODELS.items():
        if 'glm' in k:
            print(f"    {k:30s} -> {v}")
    
    print("\n[NVIDIA NIM 模型]")
    print("-" * 40)
    
    # Meta Llama
    print("  [Meta Llama 3]")
    for k, v in AVAILABLE_MODELS.items():
        if 'llama3' in k and 'llama3.' not in k:
            print(f"    {k:30s} -> {v}")
    print("  [Meta Llama 3.1]")
    for k, v in AVAILABLE_MODELS.items():
        if 'llama3.1' in k:
            print(f"    {k:30s} -> {v}")
    print("  [Meta Llama 3.2]")
    for k, v in AVAILABLE_MODELS.items():
        if 'llama3.2' in k:
            print(f"    {k:30s} -> {v}")
    
    # DeepSeek
    print("\n  [DeepSeek]")
    for k, v in AVAILABLE_MODELS.items():
        if 'deepseek' in k:
            print(f"    {k:30s} -> {v}")
    
    # Google
    print("\n  [Google Gemma]")
    for k, v in AVAILABLE_MODELS.items():
        if 'gemma' in k:
            print(f"    {k:30s} -> {v}")
    
    # Qwen
    print("\n  [Qwen]")
    for k, v in AVAILABLE_MODELS.items():
        if 'qwen' in k:
            print(f"    {k:30s} -> {v}")
    
    print("\n" + "="*60)
    print(f"总计: {len(AVAILABLE_MODELS)} 个免费模型")
    print("="*60 + "\n")

def switch_model(model_name):
    """切换模型"""
    try:
        result = subprocess.run(
            ['opencode', 'models', 'use', model_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def main():
    # 检查是否显示帮助或模型列表
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Usage: python model_router.py '你的任务描述'")
        print("       python model_router.py --list          # 显示所有可用模型")
        print("       python model_router.py --models         # 显示所有可用模型")
        print("\n示例:")
        print("  python model_router.py '重构 main_window.py'")
        print("  python model_router.py '写文档'")
        print("  python model_router.py '分析这段代码'")
        sys.exit(0)
    
    # 显示模型列表
    if len(sys.argv) >= 2 and sys.argv[1] in ['--list', '-l', '--models']:
        list_available_models()
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print("Usage: python model_router.py '你的任务描述'")
        print("       python model_router.py --list          # 显示所有可用模型")
        print("\n示例:")
        print("  python model_router.py '重构 main_window.py'")
        print("  python model_router.py '写文档'")
        print("  python model_router.py '分析这段代码'")
        sys.exit(1)
    
    user_input = ' '.join(sys.argv[1:])
    
    # 检测任务类型
    recommended_model, reason = detect_task_type(user_input)
    
    print(f"任务: {user_input}")
    print(f"检测: {reason}")
    print(f"推荐模型: {recommended_model}")
    
    # 询问是否切换
    response = input(f"\n是否切换到 {recommended_model}? [Y/n]: ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        success, output = switch_model(recommended_model)
        if success:
            print(f"已切换到 {recommended_model}")
        else:
            print(f"切换失败: {output}")
    else:
        print("保持当前模型")

if __name__ == '__main__':
    main()
