import os 
import sys 
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI
from src.api.routes import router as api_router

app = FastAPI(
    title = "Tariff Calculator API", 
    version = "0.0.1", 
)

# Include our API routes. 
app.include_router(api_router, prefix = "/api", tags = ["Tariff"])

app.get('/')
def root():
    return {"message": "Hi folks! Welcome to the Tariff Tracker"}
