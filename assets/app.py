import os
import traceback
from flask import Flask, render_template, request, redirect, jsonify

# Use absolute path for template folder to ensure it works in any working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=BASE_DIR)

messages = []

@app.route('/')
def home():
    try:
        error = request.args.get('error', '')
        return render_template("board.html", messages=messages, error=error)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

@app.route('/post', methods=["POST"])
def post():
    try:
        name = request.form.get("name", "").strip()
        msg = request.form.get("message", "").strip()
        if not name or not msg:
            return redirect("/?error=1")
        messages.append({"name": name, "msg": msg})
        return redirect("/")
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}\n{traceback.format_exc()}", 500

@app.errorhandler(500)
def internal_error(error):
    traceback.print_exc()
    return f"Internal Server Error: {str(error)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)