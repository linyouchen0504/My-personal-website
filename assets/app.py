import os
import traceback
from flask import Flask, render_template, request, redirect, jsonify

# Robust path resolution that works in both development and WSGI environments
# When running directly: __file__ is assets/app.py, so BASE_DIR is assets/
# When imported via WSGI: __file__ is still assets/app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Verify template folder exists
TEMPLATE_FOLDER = BASE_DIR
if not os.path.isdir(TEMPLATE_FOLDER):
    raise RuntimeError(f"Template folder not found: {TEMPLATE_FOLDER}")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

# Verify template file exists
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, 'board.html')
if not os.path.isfile(TEMPLATE_FILE):
    raise RuntimeError(f"Template file not found: {TEMPLATE_FILE}")

messages = []

@app.route('/')
def home():
    try:
        return render_template("board.html", messages=messages)
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
        return redirect("/")
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

@app.errorhandler(500)
def internal_error(error):
    traceback.print_exc()
    return f"Internal Server Error: {str(error)}", 500

# Only run the development server when executed directly (not in WSGI)
if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)