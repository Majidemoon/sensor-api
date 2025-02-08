from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

sensor_data = []

class SensotInput(BaseModel):
    temperature: float
    humidity: float
    pressure: float

@app.get("/")
async def root():
    return {"data" : sensor_data}

@app.post("/sensor-data/")
async def read_data(data: SensotInput):
    sensor_data.append(data)
    return {"data" : data}