import os
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)

from fastapi import APIRouter, HTTPException
from src.core.calculations import calculate_price_effects
from src.models.tariff_models import TariffRequest
import pandas as pd

router = APIRouter()

# load data on startup in main.py and pass it here...
data = pd.DataFrame()


@router.on_event("startup")
def load_data():
    global data
    data = pd.read_csv('data/working/import_intensity.csv')
@router.post("/calculate_price_effects")
def get_price_effects(payload: TariffRequest):
    if data.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")
    RESULT_DF = calculate_price_effects(
        data= data,
        new_tariffs=payload.new_tariffs,
        pass_through = payload.pass_through
    )
    return {"result": RESULT_DF.to_dict(orient="records")}