import os
import json
import time
import smtplib
import ssl
import traceback
import hashlib
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, jsonify, send_file, session
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from supabase import create_client, Client

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

# Supabase 配置
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None

# Admin credentials (password hashed with SHA-256)
ADMIN_USERNAME = "linyouchen0504"
ADMIN_PASSWORD_HASH = hashlib.sha256("l28034414".encode()).hexdigest()

# Verify template file exists
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, 'board.html')
if not os.path.isfile(TEMPLATE_FILE):
    raise RuntimeError(f"Template file not found: {TEMPLATE_FILE}")

messages = []

def get_email_config():
    """获取邮件配置信息"""
    try:
        from coze_workload_identity import Client
        client = Client()
        email_credential = client.get_integration_credential("integration-email-imap-smtp")
        return json.loads(email_credential)
    except Exception as e:
        print(f"获取邮件配置失败: {e}")
        return None

def get_ip_location(ip_address):
    """获取 IP 地址的地理位置信息"""
    try:
        # 使用 ip-api.com 免费 API 获取 IP 定位
        response = requests.get(f"http://ip-api.com/json/{ip_address}?lang=zh-CN", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = f"{data.get('country', '未知')} {data.get('regionName', '')} {data.get('city', '')}"
                return location.strip()
    except Exception as e:
        print(f"获取 IP 定位失败: {e}")
    return "未知位置"

def send_admin_login_notification(ip_address, login_time):
    """发送管理员登录通知邮件"""
    try:
        config = get_email_config()
        if not config:
            print("邮件配置不可用")
            return
        
        location = get_ip_location(ip_address)
        
        subject = "新设备登录管理员账号通知"
        content = f"时间：{login_time}\nIP：{ip_address}\n位置：{location}"
        
        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = formataddr(("管理员系统", config["account"]))
        msg["To"] = "3108908894@qq.com"
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ctx, timeout=30) as server:
            server.ehlo()
            server.login(config["account"], config["auth_code"])
            server.sendmail(config["account"], ["3108908894@qq.com"], msg.as_string())
            server.quit()
        
        print(f"管理员登录通知邮件已发送")
    except Exception as e:
        print(f"发送邮件失败: {e}")
        traceback.print_exc()

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
        # 检查用户是否已登录
        if 'user_email' not in session:
            return redirect('/')
        
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

# Supabase Auth routes
@app.route('/api/supabase-config')
def supabase_config():
    """获取 Supabase 配置（公开接口，仅返回 URL 和 anon key）"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return jsonify({"error": "Supabase credentials not configured"}), 500
    return jsonify({"url": SUPABASE_URL, "anonKey": SUPABASE_ANON_KEY})

@app.route('/api/auth/signup', methods=["POST"])
def auth_signup():
    """用户注册"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"error": "邮箱和密码不能为空"}), 400
        
        if not supabase:
            return jsonify({"error": "Supabase 未配置"}), 500
        
        response = supabase.auth.sign_up({"email": email, "password": password})
        
        if response.user:
            return jsonify({"message": "注册成功", "user": {"email": response.user.email}})
        else:
            return jsonify({"error": "注册失败"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=["POST"])
def auth_login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"error": "邮箱和密码不能为空"}), 400
        
        if not supabase:
            return jsonify({"error": "Supabase 未配置"}), 500
        
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.session:
            return jsonify({
                "message": "登录成功",
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {"email": response.user.email}
                }
            })
        else:
            return jsonify({"error": "登录失败"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=["POST"])
def auth_logout():
    """用户登出"""
    try:
        if not supabase:
            return jsonify({"error": "Supabase 未配置"}), 500
        
        # 从 header 获取 token
        token = request.headers.get('x-session', '')
        if token:
            supabase.auth.set_session(token, '')
            supabase.auth.sign_out()
        
        return jsonify({"message": "登出成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/verify', methods=["POST"])
def auth_verify():
    """验证登录态"""
    try:
        token = request.headers.get('x-session', '')
        if not token:
            return jsonify({"authenticated": False, "error": "未提供 token"}), 401
        
        if not supabase:
            return jsonify({"authenticated": False, "error": "Supabase 未配置"}), 500
        
        # 使用 service key 验证 token
        service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else supabase
        user_response = service_client.auth.get_user(token)
        
        if user_response.user:
            return jsonify({
                "authenticated": True,
                "user": {"email": user_response.user.email}
            })
        else:
            return jsonify({"authenticated": False, "error": "token 无效"}), 401
    except Exception as e:
        return jsonify({"authenticated": False, "error": str(e)}), 401

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
        
        # 获取客户端 IP 和登录时间
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 异步发送邮件通知（避免阻塞）
        try:
            send_admin_login_notification(ip_address, login_time)
        except Exception as e:
            print(f"发送登录通知邮件失败: {e}")
        
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