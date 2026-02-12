#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生产部署脚本

用于准备生产环境部署包
"""

import os
import shutil
import sys
from datetime import datetime


# 部署配置
DEPLOY_DIR = "deploy"
APP_NAME = "InterSystemsQueryTool"
VERSION = "1.0.0"


def clean_deploy_dir():
    """清理部署目录"""
    if os.path.exists(DEPLOY_DIR):
        print(f"清理部署目录: {DEPLOY_DIR}")
        shutil.rmtree(DEPLOY_DIR)
    os.makedirs(DEPLOY_DIR)


def copy_source_files():
    """复制源代码文件"""
    print("复制源代码...")
    
    # 需要复制的目录
    dirs_to_copy = [
        "src",
        "config",
        "widgets",
    ]
    
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            dest = os.path.join(DEPLOY_DIR, dir_name)
            shutil.copytree(dir_name, dest)
            print(f"  复制: {dir_name}/")
    
    # 需要复制的文件
    files_to_copy = [
        "requirements.txt",
        "config.json",
        "desktop_app.py",
        "README.md",
    ]
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy2(file_name, DEPLOY_DIR)
            print(f"  复制: {file_name}")


def create_launcher():
    """创建启动脚本"""
    print("创建启动脚本...")
    
    # Windows 批处理脚本
    bat_content = """@echo off
chcp 65001 >nul
echo 正在启动 InterSystems Query Tool...
echo.
python desktop_app.py
pause
"""
    
    bat_path = os.path.join(DEPLOY_DIR, "start.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"  创建: start.bat")
    
    # PowerShell 脚本
    ps_content = """# InterSystems Query Tool 启动脚本
Write-Host "正在启动 InterSystems Query Tool..." -ForegroundColor Green
python desktop_app.py
"""
    
    ps_path = os.path.join(DEPLOY_DIR, "start.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write(ps_content)
    print(f"  创建: start.ps1")
    
    # Python 直接启动脚本
    py_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InterSystems Query Tool 启动器
"""
import sys
sys.path.insert(0, ".")
from desktop_app import main
if __name__ == "__main__":
    main()
'''
    
    py_path = os.path.join(DEPLOY_DIR, "start.py")
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_content)
    print(f"  创建: start.py")


def create_production_config():
    """创建生产环境配置模板"""
    print("创建生产配置模板...")
    
    config_content = """{
    "database": {
        "server": "生产服务器地址",
        "port": 1972,
        "namespace": "USER",
        "username": "",
        "password": "",
        "db_type": "IRIS"
    },
    "application": {
        "name": "InterSystems Query Tool",
        "version": "1.0.0",
        "log_level": "INFO"
    },
    "ui": {
        "default_window_width": 1200,
        "default_window_height": 800,
        "min_window_width": 800,
        "min_window_height": 600
    }
}
"""
    
    config_path = os.path.join(DEPLOY_DIR, "config.json.example")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"  创建: config.json.example")


def create_install_script():
    """创建安装脚本"""
    print("创建安装脚本...")
    
    install_content = """@echo off
chcp 65001 >nul
echo ==========================================
echo InterSystems Query Tool - 安装程序
echo ==========================================
echo.

echo 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo Python 环境正常
echo.

echo 安装依赖包...
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
if errorlevel 1 (
    echo [警告] 依赖安装可能遇到问题，请检查网络连接
    pause
)

echo.
echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 请编辑 config.json 配置数据库连接信息
echo 然后运行 start.bat 启动程序
echo.
pause
"""
    
    install_path = os.path.join(DEPLOY_DIR, "install.bat")
    with open(install_path, "w", encoding="utf-8") as f:
        f.write(install_content)
    print(f"  创建: install.bat")


def create_readme():
    """创建部署说明文档"""
    print("创建部署说明...")
    
    readme_content = """# InterSystems Query Tool - 生产部署包

## 部署步骤

### 1. 环境要求
- Windows 7/10/11
- Python 3.8 或更高版本
- 网络连接（用于安装依赖）

### 2. 安装步骤

#### 方式一：使用安装脚本
1. 解压部署包到目标目录
2. 双击运行 `install.bat`
3. 根据提示完成安装

#### 方式二：手动安装
1. 解压部署包到目标目录
2. 打开命令提示符，进入部署目录
3. 执行: `pip install -r requirements.txt`
4. 编辑 `config.json` 配置数据库连接

### 3. 配置数据库连接

编辑 `config.json` 文件，配置数据库连接信息。

### 4. 启动程序

双击运行 `start.bat` 或在命令行执行:
```
python desktop_app.py
```

## 目录结构

```
├── src/                    # 源代码
├── config/                 # 配置文件
├── widgets/                # UI组件
├── desktop_app.py          # 主程序入口
├── config.json            # 应用配置
├── requirements.txt       # 依赖列表
├── start.bat              # Windows启动脚本
├── start.ps1              # PowerShell启动脚本
├── install.bat            # 安装脚本
└── README.md              # 说明文档
```

## 注意事项

1. 首次使用前必须配置正确的数据库连接信息
2. 密码会加密存储在配置文件中
3. 日志文件保存在应用目录的 logs/ 文件夹中
4. 建议使用虚拟环境部署

## 技术支持

如有问题，请联系技术支持团队。

---
生成时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n版本: " + VERSION
    
    readme_path = os.path.join(DEPLOY_DIR, "部署说明.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"  创建: 部署说明.md")


def create_deploy_package():
    """创建部署包"""
    print("=" * 50)
    print(f"开始创建生产部署包")
    print(f"应用名称: {APP_NAME}")
    print(f"版本: {VERSION}")
    print("=" * 50)
    print()
    
    # 清理并创建部署目录
    clean_deploy_dir()
    
    # 复制文件
    copy_source_files()
    print()
    
    # 创建启动脚本
    create_launcher()
    print()
    
    # 创建生产配置模板
    create_production_config()
    print()
    
    # 创建安装脚本
    create_install_script()
    print()
    
    # 创建说明文档
    create_readme()
    print()
    
    # 打包
    zip_name = f"{APP_NAME}_v{VERSION}_{datetime.now().strftime('%Y%m%d')}.zip"
    print(f"正在打包: {zip_name}")
    shutil.make_archive(
        zip_name.replace(".zip", ""),
        "zip",
        DEPLOY_DIR
    )
    print(f"部署包已创建: {zip_name}")
    print()
    print("=" * 50)
    print("生产部署包准备完成！")
    print("=" * 50)


if __name__ == "__main__":
    try:
        create_deploy_package()
    except Exception as e:
        print(f"部署包创建失败: {e}")
        sys.exit(1)
