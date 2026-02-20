import time
import json
import urllib.request
from urllib.error import URLError
import socket
import os
import csv
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db


ESP_URL = "http://192.168.4.1/api"
CSV_PATH = "tmf_readings.csv"
DEVICE_ID = "tmf_bed_1"

SERVICE_ACCOUNT_PATH = "service-account.json"
DATABASE_URL = "https://tmf-epics-default-rtdb.firebaseio.com"


def init_firebase():
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL
    })
    return db.reference("/tmf/readings")


def ensure_csv(path):
    if not os.path.isfile(path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "timestamp",
                "device_id",
                "soil_raw",
                "temperature_c",
                "humidity",
            ])

def append_csv(path, device_id, soil_raw, temp_c, humidity):
    ensure_csv(path)
    ts = datetime.now().isoformat()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, device_id, soil_raw, temp_c, humidity])

def poll_esp32():
    with urllib.request.urlopen(ESP_URL, timeout=2) as r:
        data = json.loads(r.read().decode())
    return data


def main():
    readings_ref = init_firebase()
    print("Firebase started, starting loop...")

    while True:
        try:
            data = poll_esp32()
            print("ESP32 data:", data)

            soil_raw = data.get("soil_raw")
            temp_c = data.get("temp_c")
            humidity = data.get("humidity")

            append_csv(CSV_PATH, DEVICE_ID, soil_raw, temp_c, humidity)

            reading = {
                "timestamp": datetime.now().isoformat(),
                "device_id": DEVICE_ID,
                "soil_raw": soil_raw,
                "temperature_c": temp_c,
                "humidity": humidity,
            }
            readings_ref.push(reading)

        except (URLError, socket.timeout) as e:
            print("ESP32 request failed:", e)
        except Exception as e:
            print("Unexpected error:", repr(e))

        time.sleep(10)

if __name__ == "__main__":
    main()