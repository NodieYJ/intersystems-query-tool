#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能模型切换器
根据任务类型自动选择最优模型
"""

import sys
import subprocess

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
    if len(sys.argv) < 2:
        print("Usage: python model_router.py '你的任务描述'")
        print("\n示例:")
        print("  python model_router.py '重构 main_window.py'")
        print("  python model_router.py '写文档'")
        sys.exit(1)
    
    user_input = ' '.join(sys.argv[1:])
    
    # 检测任务类型
    recommended_model, reason = detect_task_type(user_input)
    
    print(f"📝 任务: {user_input}")
    print(f"🔍 {reason}")
    print(f"🤖 推荐模型: {recommended_model}")
    
    # 询问是否切换
    response = input(f"\n是否切换到 {recommended_model}? [Y/n]: ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        success, output = switch_model(recommended_model)
        if success:
            print(f"✅ 已切换到 {recommended_model}")
        else:
            print(f"❌ 切换失败: {output}")
    else:
        print("保持当前模型")

if __name__ == '__main__':
    main()
