from flask import Flask, Response, render_template, jsonify
import cv2
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "events.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/events")
def events():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT 50"
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/image/<path:filename>")
def serve_image(filename):
    from flask import send_from_directory
    return send_from_directory("captures", os.path.basename(filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)