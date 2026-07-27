import os
import traceback
import hashlib
from flask import Flask, render_template, request, redirect, jsonify, send_file, session

# Robust path resolution that works in both development and WSGI environments
# When running directly: __file__ is assets/app.py, so BASE_DIR is assets/
# When imported via WSGI: __file__ is still assets/app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Verify template folder exists
TEMPLATE_FOLDER = BASE_DIR
if not os.path.isdir(TEMPLATE_FOLDER):
    raise RuntimeError(f"Template folder not found: {TEMPLATE_FOLDER}")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
app.secret_key = os.urandom(24)

# Admin credentials (password hashed with SHA-256)
ADMIN_USERNAME = "linyouchen0504"
ADMIN_PASSWORD_HASH = hashlib.sha256("l28034414".encode()).hexdigest()

# Verify template file exists
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, 'board.html')
if not os.path.isfile(TEMPLATE_FILE):
    raise RuntimeError(f"Template file not found: {TEMPLATE_FILE}")

messages = []

@app.route('/')
def home():
    try:
        play_music = request.args.get('play', '') == '1'
        play_video = request.args.get('video', '') == '1'
        return render_template("board.html", messages=messages, play_music=play_music, play_video=play_video)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

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
    audio_path = os.path.join(BASE_DIR, "Samuel Kim、Lorien - I Really Want to Stay at Your House.mp3")
    if os.path.isfile(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    return "Audio not found", 404

@app.route('/video')
def serve_video():
    video_path = os.path.join(BASE_DIR, "原神 《云·原神》动画短片——第二篇 来来来来，来进入《云·原神》！一键开启异世冒险！ 演唱：多多、宴宁 - 抖音.mp4")
    if os.path.isfile(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return "Video not found", 404

# Admin routes
@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return render_template("board.html", messages=[], admin_login=True, admin_error=None)
    return render_template("board.html", messages=messages, admin_panel=True)

@app.route('/admin/login', methods=["POST"])
def admin_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
        session['admin_logged_in'] = True
        return redirect("/admin")
    else:
        return render_template("board.html", messages=[], admin_login=True, admin_error="用户名或密码错误")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect("/admin")

@app.route('/admin/delete/<int:index>')
def admin_delete(index):
    if not session.get('admin_logged_in'):
        return redirect("/admin")
    if 0 <= index < len(messages):
        messages.pop(index)
    return redirect("/admin")

# Only run the development server when executed directly (not in WSGI)
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)