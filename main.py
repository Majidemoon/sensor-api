from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, SensorData
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
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

def create_plot(x, y, label):
    plt.plot(x, y, label=label, color='y')
    
    # Chart Settings
    fig = plt.gca()
    fig.set_facecolor('black')
    
    #plt.figure(figsize=(10, 5))
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    plt.xlim(start_time, end_time)
    plt.title("Sensor data Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save matplotlib as file
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return image_base64

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
       
        temperatures_plot = create_plot(timestamps, temperatures, "Temperatures (C)")
        humidity_plot = create_plot(timestamps, humidity, "Humidity (%)")
        pressure_plot = create_plot(timestamps, pressure, "Pressure (hPa)")


        html_content = f"""
<html>
    <head>
        <title>Sensor Data Plot</title>
    </head>
    <body>
        <h1>Sensor Data Plot</h1>
        <img src="data:image/png;base64,{temperatures_plot}" alt="Sensor Data Plot">
        <img src="data:image/png;base64,{humidity_plot}" alt="Sensor Data Plot">
        <img src="data:image/png;base64,{pressure_plot}" alt="Sensor Data Plot">
    </body>
</html>
"""

        return HTMLResponse(content=html_content, status_code=200)
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