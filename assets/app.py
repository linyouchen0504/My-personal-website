import os
from flask import Flask, render_template, request, redirect

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

messages = []

@app.route('/')
def home():
    return render_template("board.html", messages=messages)

@app.route('/post', methods=["POST"])
def post():
    name = request.form.get("name")
    msg = request.form.get("message")
    messages.append({"name": name, "msg": msg})
    return redirect("/")

if __name__ == '__main__':
    port = int(os.environ.get('DEPLOY_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)