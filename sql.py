import sqlite3
import random
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect("sensor.db")

cur = conn.cursor()

cur.execute("DELETE FROM sensor_data")

time = datetime.now(timezone.utc)

for i in range(1000):
    cur.execute("INSERT INTO sensor_data (temperature, humidity, pressure, timestamp) VALUES (?, ?, ?, ?)", (
        random.randint(-20, 60),
        random.randint(0, 100),
        random.randint(1, 100),
        time.isoformat()
    ))
    conn.commit()
    time += timedelta(seconds=1)

cur.close()
conn.close()