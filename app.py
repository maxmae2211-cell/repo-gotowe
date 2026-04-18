from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/get")
def get_post():
    return jsonify({
        "message": "GET OK",
        "status": "success"
    }), 200

@app.post("/post")
def create_post():
    data = request.json
    return jsonify({
        "message": "POST OK",
        "received": data
    }), 201

if __name__ == "__main__":
    # Tryb developerski (do testów ręcznych)
    app.run(host="0.0.0.0", port=8000, debug=False)
