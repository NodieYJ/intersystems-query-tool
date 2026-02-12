# PyWindows 桌面应用程序

## Docker 容器化配置

### 构建镜像

```bash
docker build -t pywindows:latest .
```

### 运行容器

```bash
# 基础运行
docker run -it --rm pywindows:latest

# 带显示转发（Linux/Mac）
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix pywindows:latest

# 带配置文件
docker run -it --rm -v $(pwd)/config:/app/config pywindows:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  pywindows:
    build: .
    image: pywindows:latest
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
```

### PyInstaller 构建

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建可执行文件
pyinstaller --onefile --windowed --name PyWindows src/main.py

# 输出在 dist/PyWindows.exe
```
