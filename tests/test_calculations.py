import pytest
import pandas as pd
import os 
import sys
from pathlib import Path 
import country_converter as coco
ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)

from src.core.calculations import calculate_price_effects

def test_calculate_price_effects():
    sample_data = pd.DataFrame({
        'ISO-A3': ['MEX', 'CAN'],
        'tariff': [0.05, 0.02],
        'trade_openness_wt_expShare': [0.3, 0.2]
    })
    new_tariffs = {'MEX': 0.25, 'CAN': 0.25}
    result = calculate_price_effects(sample_data, new_tariffs, 1.0)
    assert not result.empty
    assert set(result['ISO-A3'])== {'MEX', 'CAN'}
    return result

