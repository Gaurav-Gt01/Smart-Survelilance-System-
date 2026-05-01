import serial
import serial.tools.list_ports
import cv2
import datetime
import os
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from ultralytics import YOLO

# ── CONFIG ─────────────────────────────────────────────
SERIAL_PORT = "/dev/cu.usbserial-1130"
BAUD_RATE     = 115200
EMAIL_SENDER  = "xxxxxxxx@gmail.com"
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
EMAIL_RECEIVER = "xxxxxxxxxxx@gmail.com"
CAPTURES_DIR  = "captures"
DB_PATH       = "events.db"
# ───────────────────────────────────────────────────────

if not os.path.exists(CAPTURES_DIR):
    os.makedirs(CAPTURES_DIR)

# Init YOLO
model = YOLO("yolov8n.pt")  # Downloads automatically on first run

# Init DB
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""
  CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    classification TEXT,
    image_path TEXT
  )
""")
conn.commit()

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Camera capture failed")
        return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CAPTURES_DIR, f"capture_{ts}.jpg")
    cv2.imwrite(path, frame)
    return path, frame, ts

def classify_image(frame):
    results = model(frame)
    labels = []
    for r in results:
        for cls_id in r.boxes.cls:
            name = model.names[int(cls_id)]
            if name == "person":
                labels.append("Human")
            elif name in ["cat","dog","bird","horse","cow","sheep","bear","elephant","zebra","giraffe"]:
                labels.append("Animal")
    if "Human" in labels:
        return "Human"
    elif "Animal" in labels:
        return "Animal"
    return "Unknown"

def send_email(image_path, classification, timestamp):
    msg = MIMEMultipart()
    msg["Subject"] = f"[Alert] Motion detected — {classification}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER

    body = f"""
Motion detected by your surveillance system.

Time:           {timestamp}
Classification: {classification}

Image is attached.
"""
    msg.attach(MIMEText(body))

    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename=os.path.basename(image_path))
        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email sent.")

def log_event(timestamp, classification, image_path):
    conn.execute(
        "INSERT INTO events (timestamp, classification, image_path) VALUES (?,?,?)",
        (timestamp, classification, image_path)
    )
    conn.commit()

def handle_motion():
    print("MOTION detected — capturing image...")
    result = capture_image()
    if result is None:
        return
    image_path, frame, ts = result
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    classification = classify_image(frame)
    print(f"Classified as: {classification}")
    log_event(timestamp, classification, image_path)
    send_email(image_path, classification, timestamp)

# ── Main serial loop ──
print("Listening on serial port...")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            print(f"ESP32: {line}")
        if line == "MOTION":
            handle_motion()
except KeyboardInterrupt:
    print("Stopped.")
