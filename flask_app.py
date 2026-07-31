import os
import json
import time
import smtplib
import ssl
import traceback
import hashlib
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_file, session
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

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
app.secret_key = os.urandom(24)

# Admin credentials (password hashed with SHA-256)
ADMIN_USERNAME = "linyouchen0504"
ADMIN_PASSWORD_HASH = hashlib.sha256("l28034414".encode()).hexdigest()

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

# ==================== 公告管理 ====================
ANNOUNCEMENTS_DIR = os.path.join(BASE_DIR, "assets", "announcements")
os.makedirs(ANNOUNCEMENTS_DIR, exist_ok=True)

def load_announcements():
    """加载所有公告"""
    announcements = []
    if os.path.exists(ANNOUNCEMENTS_DIR):
        for filename in os.listdir(ANNOUNCEMENTS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(ANNOUNCEMENTS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['id'] = filename.replace('.json', '')
                        announcements.append(data)
                except:
                    pass
    # 按时间排序，最新的在前
    announcements.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return announcements

def save_announcement(announcement):
    """保存公告"""
    announcement_id = str(int(time.time()))
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{announcement_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    return announcement_id

@app.route('/api/announcements', methods=['GET'])
def api_get_announcements():
    """获取所有公告"""
    announcements = load_announcements()
    return jsonify(announcements)

@app.route('/api/announcements', methods=['POST'])
def api_create_announcement():
    """创建公告"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': '标题和正文不能为空'}), 400
    
    announcement = {
        'title': data['title'],
        'content': data['content'],
        'type': data.get('type', 'normal'),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    announcement_id = save_announcement(announcement)
    return jsonify({'id': announcement_id, 'message': '公告创建成功'})

@app.route('/api/announcements/<announcement_id>', methods=['PUT'])
def api_update_announcement(announcement_id):
    """更新公告"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未登录'}), 401
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{announcement_id}.json")
    if not os.path.exists(filepath):
        return jsonify({'error': '公告不存在'}), 404
    
    data = request.json
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': '标题和正文不能为空'}), 400
    
    announcement = {
        'id': announcement_id,
        'title': data['title'],
        'content': data['content'],
        'type': data.get('type', 'normal'),
        'created_at': data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    
    return jsonify({'message': '公告更新成功'})

@app.route('/api/announcements/<announcement_id>', methods=['DELETE'])
def api_delete_announcement(announcement_id):
    """删除公告"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未登录'}), 401
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{announcement_id}.json")
    if not os.path.exists(filepath):
        return jsonify({'error': '公告不存在'}), 404
    
    os.remove(filepath)
    return jsonify({'message': '公告删除成功'})

@app.route('/admin/announcement/add', methods=['POST'])
def admin_add_announcement():
    """添加公告（表单提交）"""
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    ann_type = request.form.get('type', 'normal')
    
    if not title or not content:
        return redirect('/admin?error=公告标题和正文不能为空')
    
    if ann_type not in ['normal', 'important']:
        ann_type = 'normal'
    
    announcements = get_announcements()
    new_id = max([a['id'] for a in announcements], default=0) + 1
    
    announcement = {
        'id': new_id,
        'title': title,
        'content': content,
        'type': ann_type,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{new_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    
    return redirect('/admin')

@app.route('/admin/announcement/delete/<int:announcement_id>', methods=['GET', 'POST'])
def admin_delete_announcement(announcement_id):
    """删除公告（表单提交）"""
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    filepath = os.path.join(ANNOUNCEMENTS_DIR, f"{announcement_id}.json")
    if not os.path.exists(filepath):
        return redirect('/admin?error=公告不存在')
    
    os.remove(filepath)
    return redirect('/admin')

# 仅开发环境运行
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
