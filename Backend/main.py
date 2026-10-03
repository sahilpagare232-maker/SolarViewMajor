from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Coordinates(BaseModel):
    sw_lat: float
    sw_lng: float
    ne_lat: float
    ne_lng: float


class AreaData(BaseModel):
    coordinates: Coordinates


@app.post("/api/area")
def receive_area(area: AreaData):
    print("Received area:", area)

    return {
        "status": "success",
        "message": "Area received",
        "area": area.coordinates.model_dump()
    }