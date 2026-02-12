#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目安装配置文件
"""

from setuptools import setup, find_packages
import os
import sys

# 获取项目根目录
project_root = os.path.abspath(os.path.dirname(__file__))

# 读取README文件内容
with open(os.path.join(project_root, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取requirements.txt文件内容
with open(os.path.join(project_root, 'requirements.txt'), 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='pywindows',
    version='1.0.0',
    description='功能完整的桌面窗体应用程序',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/example/pywindows',
    author='Author Name',
    author_email='author@example.com',
    license='MIT',
    python_requires=">=3.8,<3.9",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Operating System :: Microsoft :: Windows',
    ],
    keywords='desktop application pyside2 gui',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.12',
            'flake8>=4.0',
            'black>=21.0',
            'isort>=5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'pywindows=main:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/example/pywindows/issues',
        'Source': 'https://github.com/example/pywindows',
    },
)
