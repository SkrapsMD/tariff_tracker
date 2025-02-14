import os
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)

from fastapi import APIRouter, HTTPException, FastAPI
from src.core.calculations import calculate_price_effects
from src.models.tariff_models import TariffRequest, CountryInfoResponse
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
    print("Received Old Tariffs:", payload.old_tariffs) #
    try:
        RESULT_DF = calculate_price_effects(
            data=data,
            new_tariffs=payload.new_tariffs,
            old_tariffs=payload.old_tariffs,
            pass_through=payload.pass_through
        )
        results_list = RESULT_DF.to_dict(orient="records")
        return {"result": results_list}
    except Exception as e:
        print(f"Error in calculation: {str(e)}")  # Debug any errors
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/country_info', response_model = CountryInfoResponse)
def  get_country_info(iso:str):
    row = data.loc[data['ISO_A3'] == iso.upper()]
    if row.empty:
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryInfoResponse(
        iso = iso.upper(),
        current_tariff = round(float(row["tariff"].iloc[0]), 2),
        import_intensity = round(float(row["trade_openness_wt_expShare"].iloc[0]), 2),
        default_pass_through = 1.0
    )