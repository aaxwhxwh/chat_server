from flask import Flask, request


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/work/callback", methods=["POST"])
def work_callback():
    print(request.content)
    return "<p>Hello, World!</p>"
