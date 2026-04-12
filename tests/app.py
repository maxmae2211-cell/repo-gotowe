from flask import Flask, request
import time

app = Flask(__name__)

@app.before_request
def log_request():
    print(f"[REQ] {time.time()} {request.method} {request.path} {request.data}")
