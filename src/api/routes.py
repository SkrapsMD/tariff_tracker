import os
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)

from fastapi import APIRouter, HTTPException, FastAPI
from src.core.calculations import calculate_price_effects
from src.models.tariff_models import TariffRequest
from contextlib import asynccontextmanager
import pandas as pd

router = APIRouter(prefix="/api")

# load data on startup in main.py and pass it here...
data = pd.DataFrame()  # Initialize empty

@asynccontextmanager
async def load_data(app: FastAPI):
    global data
    try:
        data = pd.read_csv('data/working/import_intensity.csv')
        print("Data loaded successfully")  # Debug log
        yield
    finally:
        data = pd.DataFrame()  # Clean up


@router.post("/calculate_price_effects")
def get_price_effects(payload: TariffRequest):
    if data.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    print("Input data columns:", data.columns)  # Debug what columns we have
    print("Received tariffs:", payload.new_tariffs)  # Debug the incoming payload
    try:
        RESULT_DF = calculate_price_effects(
            data=data,
            new_tariffs=payload.new_tariffs,
            pass_through=payload.pass_through
        )
        return {"result": RESULT_DF.to_dict(orient="records")}
    except Exception as e:
        print(f"Error in calculation: {str(e)}")  # Debug any errors
        raise HTTPException(status_code=500, detail=str(e))