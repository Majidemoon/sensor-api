from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, SensorData
from datetime import datetime, timezone

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
        sensors = db.query(SensorData).all()
        return [
            {
                "temperature": s.temperature,
                "humidity": s.humidity,
                "pressure": s.pressure,
                "timestamp": s.timestamp.isoformat()
            }
            for s in sensors
        ]
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