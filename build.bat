@echo off
REM ========================================================================
REM Windows 本地构建脚本
REM 用于将应用程序打包为可执行文件
REM ========================================================================

echo ================================================================
echo InterSystems 数据库查询工具 - 本地构建
echo ================================================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在 PATH 中
    echo 请安装 Python 3.8+: https://python.org
    pause
    exit /b 1
)

echo [INFO] 检查依赖安装...

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] 安装 PyInstaller...
    pip install pyinstaller
)

REM 清理旧的构建文件
echo [INFO] 清理旧构建文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 执行构建
echo [INFO] 开始构建...
pyinstaller --onefile --windowed --name "InterSystemsQueryTool" src/main.py

REM 检查构建结果
if exist "dist\InterSystemsQueryTool.exe" (
    echo ================================================================
    echo [SUCCESS] 构建成功!
    echo ================================================================
    echo 可执行文件位置: dist\InterSystemsQueryTool.exe
    echo.
    echo 分发说明:
    echo  1. 将 dist\InterSystemsQueryTool.exe 分发给用户
    echo  2. 用户无需安装 Python 即可运行
    echo  3. 首次运行可能需要几秒钟启动
    echo.
    echo 提示: 可添加图标文件 (icon.ico) 来自定义图标
    echo   修改 pyinstaller.spec 中的 icon=None
    echo ================================================================
) else (
    echo [ERROR] 构建失败，请检查错误信息
    pause
    exit /b 1
)

pause
