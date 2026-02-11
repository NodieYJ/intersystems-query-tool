@echo off

rem 离线环境依赖安装脚本
rem 此脚本用于在没有网络连接的环境中安装项目依赖

echo ===========================
echo 离线环境依赖安装脚本
echo ===========================
echo.
echo 正在设置pip配置...

rem 设置PIP_CONFIG_FILE环境变量，指向本地pip配置文件
set PIP_CONFIG_FILE=%~dp0pip.ini

rem 验证pip配置
pip config list

echo.
echo 正在从本地目录安装依赖包...
echo 依赖包目录: %~dp0dependencies

echo.
rem 使用本地依赖包安装
pip install --no-index --find-links=%~dp0dependencies -r %~dp0requirements.txt

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===========================
    echo 依赖安装成功！
    echo ===========================
    echo.
    echo 现在您可以运行以下命令启动应用程序：
    echo python desktop_app.py
    echo.
) else (
    echo.
    echo ===========================
    echo 依赖安装失败！
    echo ===========================
    echo.
    echo 请检查以下内容：
    echo 1. 确保dependencies目录中包含所有必要的依赖包
    echo 2. 确保您的Python版本与依赖包兼容
    echo 3. 确保您有足够的权限安装依赖包
    echo.
    pause
    exit /b 1
)

rem 暂停以便查看输出
pause
