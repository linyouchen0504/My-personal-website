import os
import traceback
from flask import Flask, render_template, request, redirect

# PythonAnywhere 部署：模板文件应该放在 templates 目录中
# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 尝试多个可能的模板位置
TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates'),  # 标准 Flask 结构
    BASE_DIR,                              # 与 app.py 同目录
    os.path.join(BASE_DIR, 'assets'),      # assets 目录
]

# 找到第一个存在的模板目录
template_folder = None
for dir_path in TEMPLATE_DIRS:
    if os.path.isdir(dir_path) and os.path.isfile(os.path.join(dir_path, 'board.html')):
        template_folder = dir_path
        break

if template_folder is None:
    # 如果都没找到，使用 BASE_DIR 并会在运行时报错
    template_folder = BASE_DIR

app = Flask(__name__, template_folder=template_folder)

messages = []

@app.route('/')
def home():
    try:
        return render_template("board.html", messages=messages)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\nTemplate folder: {template_folder}\n{traceback.format_exc()}", 500

@app.route('/post', methods=["POST"])
def post():
    try:
        name = request.form.get("name", "").strip()
        msg = request.form.get("message", "").strip()
        # 名字为空时使用"匿名用户"
        if not name:
            name = "匿名用户"
        if not msg:
            return redirect("/")
        messages.append({"name": name, "msg": msg})
        return redirect("/")
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

@app.errorhandler(500)
def internal_error(error):
    traceback.print_exc()
    return f"Internal Server Error: {str(error)}", 500

# 仅开发环境运行
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
