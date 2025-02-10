import os 
import sys 
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.routes import router as api_router

from contextlib import asynccontextmanager
from src.api.routes import load_data
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.routes import router as api_router, load_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Properly await the async context manager
    async with load_data(app):
        print("Application startup complete")  # Debug log
        yield
        print("Application shutdown complete")  # Debug log

app = FastAPI(
    title="Tariff Calculator API",
    version="0.0.1",
    lifespan=lifespan
)

# Include our API routes. 
app.include_router(api_router)

app.mount('', StaticFiles(directory = 'frontend', html = True), name = "frontend")



app.get('/')
def root():
    return {"message": "Hi folks! Welcome to the Tariff Tracker"}
