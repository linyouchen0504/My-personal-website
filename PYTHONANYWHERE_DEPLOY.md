# PythonAnywhere 部署指南

## 问题诊断
错误日志显示：`jinja2.exceptions.TemplateNotFound: board.html`

**原因**：Flask 找不到 `board.html` 模板文件。

## 解决方案

### 方法一：标准 Flask 目录结构（推荐）

在 PythonAnywhere 上创建以下文件结构：

```
/home/linyouchen0504/mysite/
├── flask_app.py          # Flask 应用主文件
└── templates/            # 模板目录（必须叫这个名字）
    └── board.html        # 模板文件
```

**步骤**：
1. 在 PythonAnywhere 文件管理器中，进入 `/home/linyouchen0504/mysite/`
2. 创建 `templates` 文件夹
3. 将 `board.html` 上传到 `templates` 文件夹中
4. 确保 `flask_app.py` 中的模板配置正确（已更新）
5. 在 Web 配置页面重新加载应用

### 方法二：修改 flask_app.py 指定模板路径

如果你不想创建 `templates` 文件夹，可以修改 `flask_app.py` 第 16 行：

```python
# 将这一行：
app = Flask(__name__, template_folder=template_folder)

# 改为明确指定路径：
app = Flask(__name__, template_folder='/home/linyouchen0504/mysite')
```

这样 Flask 会直接在 `mysite` 目录下查找 `board.html`。

### 方法三：使用绝对路径（最简单）

在 `flask_app.py` 中直接硬编码模板路径：

```python
app = Flask(__name__, template_folder='/home/linyouchen0504/mysite')
```

## 验证步骤

1. 上传文件后，在 PythonAnywhere Bash 控制台运行：
```bash
ls -la /home/linyouchen0504/mysite/
ls -la /home/linyouchen0504/mysite/templates/
```

2. 确认文件存在后，在 Web 配置页面点击 "Reload"

3. 访问你的网站，应该能正常显示

## 文件说明

- `flask_app.py` - 已更新，支持多种模板路径查找
- `templates/board.html` - 赛博朋克风格留言板页面
- `assets/board.html` - 原始文件（可保留作为备份）
