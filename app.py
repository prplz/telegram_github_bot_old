from main import github_hook
from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=["POST"])
def wrapper():
    return github_hook(request)
