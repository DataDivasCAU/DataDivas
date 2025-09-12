from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/post-per-party")
def postPerParty():
    return render_template("post-per-party.html")

# 👉 Neue Route für /data.json
@app.route("/data.json")
def get_data():
    with open("DataDivas/Sonja/data.json", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
