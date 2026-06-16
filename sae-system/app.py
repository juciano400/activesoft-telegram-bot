import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import agent

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400
    try:
        response = agent.chat(message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    agent.reset_chat()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
