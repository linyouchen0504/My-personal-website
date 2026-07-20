import sys
import os
import traceback

# PythonAnywhere WSGI 配置文件
# 将此文件内容复制到 PythonAnywhere 的 WSGI 配置文件中

# 获取项目目录（根据你的 PythonAnywhere 用户名修改路径）
PROJECT_DIR = '/home/linyouchen0504/mysite'

# 添加项目目录到 Python 路径
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    # 导入 Flask 应用
    # 如果你的文件名是 app.py，改为：from app import app as application
    from flask_app import app as application
    
except Exception as e:
    # 导入失败时显示错误信息
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>应用导入错误</h1>
        <p><strong>错误信息:</strong> {str(e)}</p>
        <h3>堆栈跟踪:</h3>
        <pre>{traceback.format_exc()}</pre>
        <h3>调试信息:</h3>
        <ul>
            <li>PROJECT_DIR: {PROJECT_DIR}</li>
            <li>sys.path: {sys.path}</li>
            <li>文件列表: {os.listdir(PROJECT_DIR) if os.path.isdir(PROJECT_DIR) else '目录不存在'}</li>
        </ul>
        <h3>解决步骤:</h3>
        <ol>
            <li>确保 <code>flask_app.py</code> 文件存在于 {PROJECT_DIR}</li>
            <li>确保 <code>templates/board.html</code> 文件存在</li>
            <li>检查 PythonAnywhere 错误日志</li>
        </ol>
        """, 500

# PythonAnywhere 要求 WSGI 可调用对象必须命名为 'application'
