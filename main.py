from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, SensorData
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import asyncio


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
    plt.xlim(end_time, start_time)
    plt.title("Sensor data Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(False)
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


        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Sensor Data</title>
</head>
<body>
    <h2>Live Sensor Data</h2>
    <img id="temperatures_plot" src="" width="600">
    <img id="humidity_plot" src="" width="600">
    <img id="pressure_plot" src="" width="600">

    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");

        ws.onmessage = function(event) {
            const dt = event.data.split(" ");
            const img = document.getElementById("temperatures_plot");
            img.src = "data:image/png;base64," + dt[0];
            const img2 = document.getElementById("humidity_plot");
            img2.src = "data:image/png;base64," + dt[1];
            const img3 = document.getElementById("pressure_plot");
            img3.src = "data:image/png;base64," + dt[2];
        }
    </script>
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
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db : Session = Depends(get_db)):
    await websocket_task(websocket)



async def websocket_task(websocket: WebSocket):
    from database import SessionLocal

    db = SessionLocal()

    await websocket.accept()
    while True:

        try:
            sensor = db.query(SensorData).all()
            timestamps = [s.timestamp for s in sensor]
            temperatures = [s.temperature for s in sensor]
            humidity = [s.humidity for s in sensor]
            pressure = [s.pressure for s in sensor]
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

        temperatures_plot = create_plot(timestamps, temperatures, "Temperatures (C)")
        humidity_plot = create_plot(timestamps, humidity, "Humidity (%)")
        pressure_plot = create_plot(timestamps, pressure, "Pressure (hPa)")
        await websocket.send_text(f"{temperatures_plot} {humidity_plot} {pressure_plot}")

        await asyncio.sleep(0.1)