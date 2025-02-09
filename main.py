from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, SensorData
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import io
import tempfile


app = FastAPI()

class SensortInput(BaseModel):
    temperature: float
    humidity: float
    pressure: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root(db: Session = Depends(get_db)):
    try:
        # Fetch values from database
        sensor = db.query(SensorData).all()
        timestamps = [s.timestamp for s in sensor]
        temperatures = [s.temperature for s in sensor]
        humidity = [s.humidity for s in sensor]
        pressure = [s.pressure for s in sensor]

        # Create Chart from values
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, temperatures, label="Temperature (°C)", marker="o")
        plt.plot(timestamps, humidity, label="Humidity (%)", marker="s")
        plt.plot(timestamps, pressure, label="Pressure (hPa)", marker="^")

        # Chart Settings
        plt.title("Sensor data Over Time")
        plt.xlabel("Timestamp")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save matplotlib as file
        with tempfile.NamedTemporaryFile(delete=False, suffix="png") as tmpfile:
            plt.savefig(tmpfile.name, format="png")
            plt.close()
            tmpfile_path = tmpfile.name

        return FileResponse(tmpfile_path, media_type="image/png", filename="plot.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sensor-data/")
async def read_data(data: SensortInput, db : Session = Depends(get_db)):
    try:
        sensor_entry = SensorData(
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sensor_entry)
        db.commit()
        db.refresh(sensor_entry)
        return {"status": "saved", "data": data, "timestamp": sensor_entry.timestamp}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))