# PythonAnywhere 部署指南

## 1. 上传文件
将以下文件上传到 PythonAnywhere：
- `wsgi.py` (放在项目根目录)
- `assets/app.py`
- `assets/board.html`
- `assets/__init__.py`

## 2. 配置 WSGI 文件
在 PythonAnywhere 的 Web 应用配置页面，将 WSGI 配置文件路径设置为：
```
/var/www/你的用户名_pythonanywhere_com_wsgi.py
```

编辑该 WSGI 文件，内容如下：
```python
import sys
import os

# 添加项目路径
path = '/home/你的用户名/项目目录'
if path not in sys.path:
    sys.path.insert(0, path)

# 添加 assets 目录
assets_path = '/home/你的用户名/项目目录/assets'
if assets_path not in sys.path:
    sys.path.insert(0, assets_path)

# 导入 Flask 应用
from app import app as application
```

## 3. 安装依赖
在 PythonAnywhere 的 Bash 控制台中运行：
```bash
pip install flask
```

## 4. 重新加载应用
在 PythonAnywhere Web 配置页面点击 "Reload" 按钮。

## 5. 文件结构
确保文件结构如下：
```
项目目录/
── wsgi.py
└── assets/
    ├── __init__.py
    ├── app.py
    └── board.html
```

## 注意事项
- PythonAnywhere 免费版只支持 HTTP，不支持 HTTPS 自定义域名
- 确保 `board.html` 在 `assets` 目录下
- 如果修改了代码，需要点击 "Reload" 重新加载应用
