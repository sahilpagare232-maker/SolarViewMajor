from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SolarView API",
    description="Backend API for SolarView",
    version="1.0.0"
)

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "hello"
    }


@app.get("/api/test")
def test():
    return {
        "message": "Hello from FastAPI!",
        "status": "connected"
    }