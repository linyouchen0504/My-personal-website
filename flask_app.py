import os
import traceback
from flask import Flask, render_template, request, redirect, send_file

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
        play_music = request.args.get('play', '') == '1'
        play_video = request.args.get('video', '') == '1'
        return render_template("board.html", messages=messages, play_music=play_music, play_video=play_video)
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
        if "2077" in msg:
            return redirect("/?play=1")
        if "云原神" in msg:
            return redirect("/?video=1")
        return redirect("/")
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

@app.errorhandler(500)
def internal_error(error):
    traceback.print_exc()
    return f"Internal Server Error: {str(error)}", 500

@app.route('/audio')
def serve_audio():
    audio_path = os.path.join(BASE_DIR, "assets", "Samuel Kim、Lorien - I Really Want to Stay at Your House.mp3")
    if os.path.isfile(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    return "Audio not found", 404

@app.route('/video')
def serve_video():
    video_path = os.path.join(BASE_DIR, "assets", "原神 《云·原神》动画短片——第二篇 来来来来，来进入《云·原神》！一键开启异世冒险！ 演唱：多多、宴宁 - 抖音.mp4")
    if os.path.isfile(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return "Video not found", 404

# 仅开发环境运行
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
