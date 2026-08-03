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

# Announcements directory
ANNOUNCEMENTS_DIR = os.path.join(BASE_DIR, 'announcements')
if not os.path.isdir(ANNOUNCEMENTS_DIR):
    os.makedirs(ANNOUNCEMENTS_DIR)

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

# Announcement routes
@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    """获取所有公告"""
    announcements = []
    if os.path.isdir(ANNOUNCEMENTS_DIR):
        for filename in os.listdir(ANNOUNCEMENTS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(ANNOUNCEMENTS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    announcements.append(json.load(f))
    # 按时间戳排序，最新的在前
    announcements.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return jsonify(announcements)

@app.route('/api/announcements/important', methods=['GET'])
def get_important_announcements():
    """获取所有重要公告（用于首页弹窗）"""
    announcements = []
    if os.path.isdir(ANNOUNCEMENTS_DIR):
        for filename in os.listdir(ANNOUNCEMENTS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(ANNOUNCEMENTS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    announcement = json.load(f)
                    if announcement.get('type') == 'important':
                        announcements.append(announcement)
    # 按时间戳排序，最新的在前
    announcements.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return jsonify(announcements)

@app.route('/api/announcements', methods=['POST'])
def add_announcement():
    """添加新公告"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "未登录"}), 401
    
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    ann_type = data.get('type', 'normal')  # 'normal' or 'important'
    
    if not title or not content:
        return jsonify({"error": "标题和正文不能为空"}), 400
    
    # 生成唯一 ID
    timestamp = int(time.time() * 1000)
    ann_id = str(timestamp)
    
    announcement = {
        "id": ann_id,
        "title": title,
        "content": content,
        "type": ann_type,
        "timestamp": timestamp,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{ann_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    
    return jsonify(announcement), 201

@app.route('/api/announcements/<ann_id>', methods=['PUT'])
def update_announcement(ann_id):
    """更新公告"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "未登录"}), 401
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{ann_id}.json")
    if not os.path.isfile(filepath):
        return jsonify({"error": "公告不存在"}), 404
    
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    ann_type = data.get('type', 'normal')
    
    if not title or not content:
        return jsonify({"error": "标题和正文不能为空"}), 400
    
    with open(filepath, 'r', encoding='utf-8') as f:
        announcement = json.load(f)
    
    announcement['title'] = title
    announcement['content'] = content
    announcement['type'] = ann_type
    announcement['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    
    return jsonify(announcement)

@app.route('/api/announcements/<ann_id>', methods=['DELETE'])
def delete_announcement(ann_id):
    """删除公告"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "未登录"}), 401
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{ann_id}.json")
    if not os.path.isfile(filepath):
        return jsonify({"error": "公告不存在"}), 404
    
    os.remove(filepath)
    return jsonify({"success": True})

# Only run the development server when executed directly (not in WSGI)
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)